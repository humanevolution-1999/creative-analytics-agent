# Creative Agent 🧠✨

An AI-powered analytics agent that synthesizes market trends from top-performing creatives ("Winning DNA") and benchmarks your own ads against them to predict success.

## 🚀 Features
*   **Market Intelligence**: Analyzes competitor video ads to extract patterns (Pacing, mechanics, motivations).
*   **Winning DNA Synthesis**: Generates a composite profile of what works in your specific niche.
*   **Creative Benchmarking**: Scores your video against the "Winning DNA" using a 4-order framework (Motivation, Mechanics, Sensory, IP).
*   **Actionable Insights**: Provides specific tips to improve hook rate and conversion.

---

## 📖 How to Use

### Phase 1: Market Intelligence (The "Winning DNA")
To understand what works, you must first upload competitor data.

1.  **Prepare your CSV file.** It must have the following columns:
    *   `Advertiser App` (or `Advertiser App Name`)
    *   `Impression Share` (e.g., "14.5%" or "0.145")
    *   `Creative URL` (Direct link to .mp4 or .mov)
    *   *Optional:* `Duration`

2.  **Upload to Agent:**
    *   Drag & Drop your CSV into the **"Market Intelligence"** section.
    *   Wait for the agent to analyze the top 10 videos.
    *   **Result:** The agent will display a "Winning DNA" profile (Motivation, Pacing, Mechanic).

### Phase 2: Benchmarking Your Creative
Once the "Winning DNA" is established, you can test your own assets.

1.  **Upload Creative:**
    *   Drag & Drop an `.mp4` file into the **"Benchmark Creative"** section.
    *   OR paste a valid video URL.

2.  **Get Strategic Report:**
    *   The agent generates a comprehensive report comparing your ad to the market leader.
    *   **Score ($P_s$):** A probability of success score (0-100%).
    *   **Gap Analysis:** Specific recommendations (e.g., "Cut the intro by 2s", "Add fail state").

---

## 🔄 Persistence & Updates
*   **Auto-Save:** The "Winning DNA" is saved to `winning_dna.json` automatically.
*   **Refresh/Update:** 
    *   If you restart the server, the **previous benchmark loads automatically**.
    *   To start a **NEW analysis**, click the **"🔄 Update Benchmark"** button in the header and upload a new CSV.

## ⚠️ Troubleshooting
*   **"Winning DNA synthesis failed"**: Check your CSV columns. Ensure `Impression Share` and `Creative URL` are present.
*   **"Gemini API Error: 403"**: Your API key is invalid or expired. Check your environment variable.
