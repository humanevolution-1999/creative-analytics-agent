import json
import os

mock_dna = {
    "dominant_motivation": "Social Acceptance (Mock)",
    "avg_pacing": "0.5s (Mock)",
    "key_mechanic": "Swipe to Match (Mock)",
    "visual_trend": "Bright Neon Colors (Mock)"
}

file_path = "winning_dna.json"

with open(file_path, "w") as f:
    json.dump(mock_dna, f, indent=4)

print(f"✅ Mock Winning DNA written to {os.path.abspath(file_path)}")
print("Now start the server and refresh the UI to see the persisted state.")
