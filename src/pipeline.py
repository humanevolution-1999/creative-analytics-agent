import os
import time
import json
import csv
import random
import requests
import tempfile
import google.generativeai as genai
from .prompts import BENCHMARK_SYNTHESIZER_PROMPT, ANALYZER_PROMPT_TEMPLATE, VIDEO_ANALYSIS_PROMPT

# ==============================================================================
# SECTION 2: THE PIPELINE LOGIC (The "Body")
# ==============================================================================

class CreativeAnalyticsPipeline:
    def __init__(self, api_key):
        self.api_key = api_key
        if not api_key:
            raise ValueError("API Key is required for CreativeAnalyticsPipeline")
        
        # Configure the Gemini API
        genai.configure(api_key=self.api_key)
        self.model = genai.GenerativeModel('gemini-3-pro-preview') 

    def _generate_content(self, system_prompt, user_input, video_file=None):
        """
        Generates content using the Gemini model.
        """
        print(f"\n[System] Sending prompt to Gemini... (Input length: {len(str(user_input))} chars)")
        
        try:
            if video_file:
                # Gemini 1.5 Pro takes [system_prompt, video_file, user_prompt] or similar structure
                # We'll prepend the system prompt to the user input for simplicity or use system_instruction if supported
                # For this implementation, we just pass list of contents
                response = self.model.generate_content([system_prompt, video_file, user_input])
            else:
                response = self.model.generate_content([system_prompt, user_input])
            return response.text
        except Exception as e:
            print(f"Error calling Gemini API: {e}")
            raise Exception(f"Gemini API Error: {str(e)}")

    def _download_video(self, url):
        """
        Downloads a video from a URL to a temporary file.
        Returns the path to the temporary file.
        """
        print(f"   [Download] Downloading video from {url}...")
        try:
            # excessive timeout to handle larger files if needed, but keeping it reasonable for now
            response = requests.get(url, stream=True, timeout=60)
            response.raise_for_status()
            
            # Create a temp file. We used named temp file so we can pass the path to Gemini.
            # We don't delete on close so we can upload it, then we manually delete.
            tfile = tempfile.NamedTemporaryFile(delete=False, suffix=".mp4")
            
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    tfile.write(chunk)
            
            tfile.close()
            print(f"   [Download] Saved to temporary file: {tfile.name}")
            return tfile.name
        except Exception as e:
            print(f"   [Error] Failed to download video: {e}")
            return None

    def _analyze_video(self, video_path_or_url):
        """
        Analyzes a video using Gemini 1.5 Pro.
        Handles both local paths and URLs (by downloading them first).
        """
        print(f"  > Analyzing video: {video_path_or_url}")
        
        local_path = video_path_or_url
        is_temp_file = False

        # Check if it's a URL
        if video_path_or_url.startswith("http"):
            downloaded_path = self._download_video(video_path_or_url)
            if not downloaded_path:
                return {"error": "Failed to download video from URL"}
            local_path = downloaded_path
            is_temp_file = True

        # Now process the local file (either original local path or downloaded temp file)
        result = {}
        if os.path.isfile(local_path):
            print(f"   [Upload] Uploading {local_path} to Gemini...")
            try:
                video_file = genai.upload_file(path=local_path)
                
                # Wait for processing
                while video_file.state.name == "PROCESSING":
                    print(".", end="", flush=True)
                    time.sleep(2)
                    video_file = genai.get_file(video_file.name)
                
                if video_file.state.name == "FAILED":
                    print("   [Error] Video processing failed.")
                    result = {"error": "Video processing failed"}
                else: 
                    print("   [Ready] Video processed. Generating insights...")
                    
                    response_json = self._generate_content(
                        system_prompt=VIDEO_ANALYSIS_PROMPT,
                        user_input="Analyze this video.",
                        video_file=video_file
                    )
                    
                    try:
                        # Cleanup JSON markdown if present
                        cleaned_json = response_json.replace('```json', '').replace('```', '')
                        result = json.loads(cleaned_json)
                    except json.JSONDecodeError:
                        result = {"error": "Failed to parse video analysis"}
            except Exception as e:
                 print(f"   [Error] processing video: {e}")
                 result = {"error": str(e)}
        else:
            result = {"error": f"File not found: {local_path}"}
        
        # Cleanup temp file if we created one
        if is_temp_file and os.path.exists(local_path):
            print(f"   [Cleanup] Removing temporary file {local_path}")
            os.remove(local_path)

        return result

    def _parse_impression_share(self, share_str):
        """
        Parses "14.09%" or "14.09" into a float 14.09.
        Returns 0.0 if parsing fails.
        """
        if not share_str:
            return 0.0
        try:
            return float(share_str.replace('%', '').strip())
        except ValueError:
            return 0.0

    def _parse_impression_share(self, share_str):
        if not share_str:
            return 0.0
        try:
            return float(share_str.replace('%', '').strip())
        except ValueError:
            return 0.0

    def get_winning_dna(self, csv_path):
        """
        Step 1: Ingest CSV competitor data, analyze top 20 videos, and synthesize 'Winning DNA'.
        """
        print(f"\n--- Phase 1: Processing Market Data from {csv_path} ---")
        
        analyzed_data = []

        try:
            with open(csv_path, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                # Sort by Impression Share (descending)
                sorted_rows = sorted(
                    reader, 
                    key=lambda row: self._parse_impression_share(row.get('Impression Share', '0')), 
                    reverse=True
                )
                
                # Take top 10 (Increased to 10 as requested)
                top_performers = sorted_rows[:10]
                print(f"I found {len(sorted_rows)} total creatives. analyzing the top {len(top_performers)} by Impression Share.")

                for idx, row in enumerate(top_performers):
                    # Handle flexible column names (e.g. "Advertiser App" vs "Advertiser App Name")
                    app_name = row.get('Advertiser App') or row.get('Advertiser App Name') or 'Unknown App'
                    url = row.get('Creative URL', 'N/A')
                    
                    print(f"[{idx+1}/{len(top_performers)}] Processing {app_name}: {url}")
                    
                    # Simulate video analysis
                    # We check if we have a local download of it, otherwise we treat it as URL
                    video_insight = self._analyze_video(url)
                    
                    # Structure the data for the Synthesizer
                    analyzed_data.append(f"""
                    Creative #{idx+1}:
                    - App: {app_name}
                    - Stats: {row.get('Impression Share')} Share, Duration {row.get('Duration')}s
                    - Extracted Data: {json.dumps(video_insight, indent=2)}
                    """)

        except Exception as e:
            raise Exception(f"Error reading/parsing CSV: {str(e)}")

        # Combine all analyses into one massive context block
        full_market_context = "\n".join(analyzed_data)
        
        if not analyzed_data:
             raise Exception("No valid rows found in CSV. Check column headers (Advertiser App, Impression Share).")

        print("\n--- Phase 1b: Synthesizing 'Winning DNA' from Aggregate Analysis ---")
        response = self._generate_content(
            system_prompt=BENCHMARK_SYNTHESIZER_PROMPT,
            user_input=full_market_context
        )
        try:
            # Clean possible markdown code fences
            cleaned_response = response.replace('```json', '').replace('```', '')
            return json.loads(cleaned_response)
        except json.JSONDecodeError:
            raise Exception(f"LLM returned invalid JSON: {response[:100]}...")

    def build_dynamic_prompt(self, winning_dna):
        """
        Step 2: Inject the JSON DNA into the main Analyzer Prompt Template.
        """
        print("\n--- Phase 2: Building Dynamic Context ---")
        
        # Format the DNA for readability in the prompt
        dna_text_block = f"""
* **Dominant Motivation:** {winning_dna.get('dominant_motivation', 'N/A')}
* **Avg. Pacing (Cuts):** {winning_dna.get('avg_pacing', 'N/A')}
* **Key Mechanic:** {winning_dna.get('key_mechanic', 'N/A')}
* **Visual Trend:** {winning_dna.get('visual_trend', 'N/A')}
        """
        
        # Strict replacement of the placeholder
        final_prompt = ANALYZER_PROMPT_TEMPLATE.replace(
            "{benchmark_data_placeholder}", 
            dna_text_block
        )
        return final_prompt

    def analyze_creative(self, creative_file_path, raw_competitor_data):
        """
        Main Orchestrator Function.
        """
        # 1. Get the Market Truth
        winning_dna = self.get_winning_dna(raw_competitor_data)
        print(f"Generated Winning DNA: {winning_dna}")

        # 2. Build the Context-Aware Prompt
        system_prompt = self.build_dynamic_prompt(winning_dna)

        # 3. Analyze the Creative
        print("\n--- Phase 3: Analyzing Creative Asset ---")

        # Analyze the user's video file
        # This will upload it to Gemini if it's a local path
        my_ad_analysis = self._analyze_video(creative_file_path)
        
        context_for_final_analysis = f"""
        MARKET BENCHMARK (WINNING DNA):
        {json.dumps(winning_dna, indent=2)}
        
        USER CREATIVE ANALYSIS:
        {json.dumps(my_ad_analysis, indent=2)}
        """

        # 3. Generate Final Report
        print("   [Report] Generating final strategic analysis...")
        final_report = self._generate_content(
            system_prompt=system_prompt,
            user_input=context_for_final_analysis
        )
        
        return final_report
