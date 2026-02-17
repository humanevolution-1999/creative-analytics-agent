import os
import shutil
import asyncio
import json
from typing import List
from fastapi import FastAPI, File, UploadFile, BackgroundTasks, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import logging

# Import our existing pipeline
from src.pipeline import CreativeAnalyticsPipeline

# Setup Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("CreativeAgent")

app = FastAPI(title="Creative Agent Brain")

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global State (In-memory for simplicity + JSON persistence)
STATE = {
    "market_data_path": None,
    "winning_dna": None,
    "latest_analysis": None,
    "is_processing": False
}

WINNING_DNA_FILE = "winning_dna.json"

# Load saved DNA on startup
if os.path.exists(WINNING_DNA_FILE):
    try:
        with open(WINNING_DNA_FILE, "r") as f:
            STATE['winning_dna'] = json.load(f)
        logger.info("Loaded persisted Winning DNA.")
    except Exception as e:
        logger.error(f"Failed to load winning_dna.json: {e}")

# Startup Check for API Key
API_KEY = os.environ.get("GEMINI_API_KEY")
if not API_KEY:
    logger.error("GEMINI_API_KEY environment variable not set.")
    # In production, we might raise an error, but for now we'll just log it 
    # and fail gracefully inside endpoints if needed.

# Mount static files for the frontend
app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/")
def read_root():
    return FileResponse("static/index.html")

@app.get("/winning-dna")
def get_winning_dna_status():
    """
    Check if we have an existing benchmark.
    """
    if STATE['winning_dna']:
        return JSONResponse(content={"status": "success", "winning_dna": STATE['winning_dna']})
    else:
        return JSONResponse(content={"status": "not_found", "message": "No benchmark data found."})

@app.post("/upload-market-data")
async def upload_market_data(file: UploadFile = File(...)):
    """
    Step 1: Upload and parse the Competitor CSV.
    """
    try:
        file_location = f"temp_{file.filename}"
        with open(file_location, "wb+") as file_object:
            shutil.copyfileobj(file.file, file_object)
        
        STATE['market_data_path'] = file_location
        # We DO NOT reset winning_dna here yet. We wait for explicit "Analyze" action.
        # This allows users to re-upload CSV without losing old benchmark immediately if they cancel.
        
        return JSONResponse(content={
            "status": "success", 
            "message": f"Market Data '{file.filename}' received. Ready to analyze.",
            "file_path": file_location
        })
    except Exception as e:
        return JSONResponse(content={"status": "error", "message": str(e)}, status_code=500)

from fastapi import Request

@app.post("/analyze-market")
async def analyze_market(request: Request):
    """
    Step 2: Trigger Winning DNA Synthesis.
    """
    if not STATE['market_data_path']:
        return JSONResponse(content={"status": "error", "message": "No market data uploaded."}, status_code=400)
    if not API_KEY:
        return JSONResponse(content={"status": "error", "message": "Server API Key not configured."}, status_code=500)
    
    try:
        STATE['is_processing'] = True
        logger.info("Starting Market Analysis...")
        
        # Initialize Pipeline
        pipeline = CreativeAnalyticsPipeline(api_key=API_KEY)
        
        # Run Phase 1 & 2
        winning_dna = pipeline.get_winning_dna(STATE['market_data_path'])
        
        if not winning_dna:
            raise Exception("Winning DNA synthesis failed. Please check your CSV file format.")

        STATE['winning_dna'] = winning_dna
        STATE['is_processing'] = False
        
        # Persist to disk
        try:
            with open(WINNING_DNA_FILE, "w") as f:
                json.dump(winning_dna, f, indent=4)
        except Exception as e:
            logger.error(f"Failed to save winning_dna.json: {e}")
        
        return JSONResponse(content={
            "status": "success",
            "winning_dna": winning_dna
        })
    except Exception as e:
        STATE['is_processing'] = False
        return JSONResponse(content={"status": "error", "message": str(e)}, status_code=500)

class AnalyzeRequest(BaseModel):
    video_url: str = None  # Removed api_key

from fastapi.concurrency import run_in_threadpool
import aiofiles

@app.post("/analyze-creative-file")
async def analyze_creative_file(
    file: UploadFile = File(...)
):
    """
    Step 3: Upload User Creative and Benchmark it.
    """
    if not STATE['winning_dna']:
        return JSONResponse(content={"status": "error", "message": "Winning DNA not ready. Analyze market first."}, status_code=400)
    if not API_KEY:
        return JSONResponse(content={"status": "error", "message": "Server API Key not configured."}, status_code=500)
    
    try:
        # Save uploaded video asynchronously
        file_location = f"temp_creative_{file.filename}"
        
        # USE ASYNC WRITE to avoid blocking logic
        async with aiofiles.open(file_location, 'wb') as out_file:
            while content := await file.read(1024 * 1024):  # Read in 1MB chunks
                await out_file.write(content)
        
        pipeline = CreativeAnalyticsPipeline(api_key=API_KEY)
        
        # 1. Build Prompt (Fast, CPU bound, can stay or be threaded)
        system_prompt = pipeline.build_dynamic_prompt(STATE['winning_dna'])
        
        # 2. Analyze Video (Blocking I/O - Run in Threadpool)
        print("\n--- Phase 3: Analyzing Benchmark Creative ---")
        logger.info(f"Analyzing creative: {file_location}")
        
        # Offload blocking call to threadpool
        my_ad_analysis = await run_in_threadpool(pipeline._analyze_video, file_location)
        
        # 3. Generate Report (Blocking I/O - Run in Threadpool)
        context = f"""
        MARKET BENCHMARK (WINNING DNA):
        {STATE['winning_dna']}
        
        USER CREATIVE ANALYSIS:
        {my_ad_analysis}
        """
        
        final_report = await run_in_threadpool(pipeline._generate_content, system_prompt, context)
        
        # Cleanup
        if os.path.exists(file_location):
            os.remove(file_location)
        
        return JSONResponse(content={
            "status": "success",
            "report": final_report,
            "creative_analysis": my_ad_analysis
        })

    except Exception as e:
        logger.error(f"Error in analyze_creative_file: {str(e)}")
        return JSONResponse(content={"status": "error", "message": str(e)}, status_code=500)

@app.post("/analyze-creative-url")
async def analyze_creative_url(request: AnalyzeRequest):
    """
    Step 3 (Alternate): Analyze from URL.
    """
    if not STATE['winning_dna']:
        return JSONResponse(content={"status": "error", "message": "Winning DNA not ready. Analyze market first."}, status_code=400)
    if not API_KEY:
        return JSONResponse(content={"status": "error", "message": "Server API Key not configured."}, status_code=500)

    try:
        pipeline = CreativeAnalyticsPipeline(api_key=API_KEY)
        
        # 1. Build Prompt
        system_prompt = pipeline.build_dynamic_prompt(STATE['winning_dna'])
        
        # 2. Analyze Video (Downloads URL -> Temp -> Gemini)
        logger.info(f"Analyzing creative URL: {request.video_url}")
        my_ad_analysis = pipeline._analyze_video(request.video_url)
        
        if "error" in my_ad_analysis:
             return JSONResponse(content={"status": "error", "message": my_ad_analysis['error']}, status_code=400)

        # 3. Generate Report
        context = f"""
        MARKET BENCHMARK (WINNING DNA):
        {STATE['winning_dna']}
        
        USER CREATIVE ANALYSIS:
        {my_ad_analysis}
        """
        
        final_report = pipeline._generate_content(system_prompt, context)
        
        return JSONResponse(content={
            "status": "success",
            "report": final_report,
            "creative_analysis": my_ad_analysis
        })

    except Exception as e:
        return JSONResponse(content={"status": "error", "message": str(e)}, status_code=500)
