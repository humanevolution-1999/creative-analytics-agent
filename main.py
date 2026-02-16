import os
import sys
import textwrap
from src.pipeline import CreativeAnalyticsPipeline

# ==============================================================================
# SECTION 3: EXECUTION (The "Run")
# ==============================================================================

if __name__ == "__main__":
    # 0. API Key Handling
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        print("Error: GEMINI_API_KEY environment variable not set.")
        print("Please set it via: export GEMINI_API_KEY='your_key_here'")
        # For testing convenience, you could uncomment the line below:
        # api_key = input("Enter your Gemini API Key: ").strip()
        sys.exit(1)

    # 1. Initialize
    agent = CreativeAnalyticsPipeline(api_key=api_key)

    # 2. Market Data (CSV Input)
    # The agent now ingests a CSV to find the "Winning DNA"
    raw_market_data = "real-data.csv"
    if not os.path.exists(raw_market_data):
        print(f"Error: Market data file '{raw_market_data}' not found.")
        sys.exit(1)

    # 3. Your Creative (The file you want to score)
    # REPLACE THIS with your actual video file path
    my_creative = "my_new_ad_v1.mp4" 

    if not os.path.exists(my_creative):
        print(f"Warning: Creative file '{my_creative}' not found.")
        print("Please place your video file in this directory or update 'my_creative' variable in main.py")
        sys.exit(1)

    # 4. Run the Pipeline
    result = agent.analyze_creative(my_creative, raw_market_data)
    
    print("\n--- Final Agent Output ---")
    print(textwrap.dedent(result))
