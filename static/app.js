const API_URL = "http://localhost:8000";

// --- State ---
// API Key is now handled on server side
let currentAnalysisData = null; // Store analysis result for JSON export

// --- Event Listeners ---

// Drag & Drop for CSV
const csvDrop = document.getElementById("csvDropZone");
const csvInput = document.getElementById("csvInput");

csvDrop.addEventListener("click", () => csvInput.click());
csvInput.addEventListener("change", (e) => handleCsvUpload(e.target.files[0]));

csvDrop.addEventListener("dragover", (e) => {
    e.preventDefault();
    csvDrop.classList.add("dragover");
});
csvDrop.addEventListener("dragleave", () => csvDrop.classList.remove("dragover"));
csvDrop.addEventListener("drop", (e) => {
    e.preventDefault();
    csvDrop.classList.remove("dragover");
    handleCsvUpload(e.dataTransfer.files[0]);
});

// Drag & Drop for Video
const videoDrop = document.getElementById("videoDropZone");
const videoInput = document.getElementById("videoInput");

videoDrop.addEventListener("click", () => videoInput.click());
videoInput.addEventListener("change", (e) => handleCreativeUpload(e.target.files[0]));

videoDrop.addEventListener("dragover", (e) => {
    e.preventDefault();
    videoDrop.classList.add("dragover");
});
videoDrop.addEventListener("drop", (e) => {
    e.preventDefault();
    videoDrop.classList.remove("dragover");
    handleCreativeUpload(e.dataTransfer.files[0]);
});

document.getElementById("analyzeUrlBtn").addEventListener("click", () => {
    const url = document.getElementById("videoUrlInput").value;
    if (url) handleCreativeUrl(url);
});

// --- Tab Logic ---
function switchTab(tabName) {
    document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
    document.querySelectorAll('.tab-content').forEach(c => c.classList.remove('active'));

    // Simple way to just select by index or text, but here logic is specific:
    if (tabName === 'file') {
        document.querySelector('.tab:nth-child(1)').classList.add('active');
        document.getElementById('tab-file').classList.add('active');
    } else {
        document.querySelector('.tab:nth-child(2)').classList.add('active');
        document.getElementById('tab-url').classList.add('active');
    }
}
window.switchTab = switchTab; // Expose to global scope for HTML onclick

// --- API Logic ---

async function handleCsvUpload(file) {
    if (!file) return;

    const status = document.getElementById("market-status");
    status.classList.remove("hidden");

    // 1. Upload File
    const formData = new FormData();
    formData.append("file", file);

    try {
        const uploadRes = await fetch(`${API_URL}/upload-market-data`, {
            method: "POST",
            body: formData
        });
        const uploadData = await uploadRes.json();

        if (uploadData.status === "success") {
            // 2. Trigger Analysis
            const analyzeRes = await fetch(`${API_URL}/analyze-market`, {
                method: "POST"
            });
            const analyzeData = await analyzeRes.json();

            if (analyzeData.status === "success") {
                displayWinningDna(analyzeData.winning_dna);
                // Unlock next step
                document.getElementById("creative-panel").classList.remove("disabled");
            } else {
                alert("Analysis failed: " + analyzeData.message);
            }
        } else {
            alert("Upload failed: " + uploadData.message);
        }
    } catch (error) {
        console.error(error);
        alert("An error occurred.");
    } finally {
        status.classList.add("hidden");
    }
}

function displayWinningDna(dna) {
    document.getElementById("winning-dna-result").classList.remove("hidden");
    document.getElementById("dna-motivation").innerText = dna.dominant_motivation;
    document.getElementById("dna-pacing").innerText = dna.avg_pacing;
    document.getElementById("dna-mechanic").innerText = dna.key_mechanic;
}

async function handleCreativeUpload(file) {
    if (!file) return;

    startCreativeAnalysis();

    const formData = new FormData();
    formData.append("file", file);

    try {
        const res = await fetch(`${API_URL}/analyze-creative-file`, {
            method: "POST",
            body: formData
        });
        const data = await res.json();
        handleAnalysisResult(data);
    } catch (error) {
        console.error(error);
        alert("Analysis error");
    }
}

async function handleCreativeUrl(url) {
    startCreativeAnalysis();

    try {
        const res = await fetch(`${API_URL}/analyze-creative-url`, {
            method: "POST",
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ video_url: url })
        });
        const data = await res.json();
        handleAnalysisResult(data);
    } catch (error) {
        console.error(error);
        alert("Analysis error");
    }
}

function startCreativeAnalysis() {
    const status = document.getElementById("creative-status");
    status.classList.remove("hidden");
    document.getElementById("report-panel").classList.add("hidden");
}

function handleAnalysisResult(data) {
    document.getElementById("creative-status").classList.add("hidden");

    if (data.status === "success") {
        // Store for Export
        currentAnalysisData = data;

        document.getElementById("report-panel").classList.remove("hidden");
        document.getElementById("report-content").innerHTML = marked.parse(data.report);

        // Extract Score from Report (Regex matches: **Probability of Success ...:** 72%)
        const scoreMatch = data.report.match(/\*\*Probability of Success.*\:\*\* ([0-9.]+)%?/);
        if (scoreMatch && scoreMatch[1]) {
            const percentage = Math.round(parseFloat(scoreMatch[1]));

            const badge = document.getElementById("success-probability");
            badge.innerText = `${percentage}% Success`;

            // Color coding
            if (percentage >= 80) badge.style.background = "linear-gradient(135deg, #10b981 0%, #059669 100%)"; // Green
            else if (percentage >= 60) badge.style.background = "linear-gradient(135deg, #f59e0b 0%, #d97706 100%)"; // Yellow
            else badge.style.background = "linear-gradient(135deg, #ef4444 0%, #b91c1c 100%)"; // Red
        }

        // Scroll to report
        document.getElementById("report-panel").scrollIntoView({ behavior: 'smooth' });
    } else {
        alert("Analysis Failed: " + data.message);
    }
}

// --- JSON Export ---
function exportJSON() {
    if (!currentAnalysisData) {
        alert("No analysis data to export. Run an analysis or Load Demo first.");
        return;
    }

    const dataStr = JSON.stringify(currentAnalysisData, null, 4);
    const dataUri = 'data:application/json;charset=utf-8,' + encodeURIComponent(dataStr);

    const exportFileDefaultName = 'Creative_Strategy_Analysis.json';

    const linkElement = document.createElement('a');
    linkElement.setAttribute('href', dataUri);
    linkElement.setAttribute('download', exportFileDefaultName);
    linkElement.click();
}
window.exportJSON = exportJSON;

// --- DEMO DATA FOR TESTING ---
function loadDemoData() {
    const dummyReport = `
## Executive Summary
- **Probability of Success (Ps):** 85%
- **Verdict:** GO (High Potential)

## Score Breakdown Table
| Variable | Weight | Score | Justification |
| :--- | :--- | :--- | :--- |
| **Motivation (M)** | 50% | 0.9 | Strong alignment with "Cognitive Challenge" motivation. |
| **Ad Mechanics (A)** | 30% | 0.8 | Good use of "Fail State" and tension loops. |
| **Sensory (S)** | 20% | 0.8 | Visuals match market leaders (Pink/Blue palette). |
| **IP Multiplier (I)** | N/A | 1.0 | No Major IP detected. |

**Final Calculation:** Ps = ((0.9 * 0.5) + (0.8 * 0.3) + (0.8 * 0.2)) * 1.0 * 100 = 85%

## Competitive Gap Analysis
*   **Visual Pacing:** Your video is slightly slower (1.2s avg cut) compared to the market benchmark (0.8s avg cut).
*   **Mechanic Clarity:** The "Pin Pull" mechanic is clear, but the "Fail State" could be more exaggerated.

## Actionable Suggestions
1.  **Increase Pacing:** Speed up the first 3 seconds by 20% to hook users faster.
2.  **Highlight Fail State:** Add a flashing red overlay when the character fails to increase tension (Loss Aversion).
3.  **Audio Sync:** Ensure the "click" sound effects sync perfectly with the pin movement.
`;
    // Mock Data Object for JSON Export
    const mockData = {
        status: "success",
        report: dummyReport,
        analysis_timestamp: new Date().toISOString(),
        demo_mode: true
    };

    // Simulate Analysis Result
    handleAnalysisResult(mockData);
}
window.loadDemoData = loadDemoData;
