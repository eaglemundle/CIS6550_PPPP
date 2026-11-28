/**
 * @file popup.js
 * @description Frontend-to-Backend integration and local model switching logic
 *              for the CIS6550 Privacy-Preserving Prompt Protection extension.
 * @modified_by Myunghee Jung
 * @updates
 *  - Connected UI actions (/api/mask, /api/chat) to the local FastAPI backend.
 *  - Implemented dynamic local LLM model selection (Llama 3.2, Qwen 2.5, Mistral)
 *    with automatic re-generation and backend model verification (data.model_used).
 *  - Added latency tracking and error handling for offline/unpulled Ollama models.
 */

const API = "http://127.0.0.1:8000";

let selectedModel = "llama3.2:3b";
let maskedText = "";
let mappings = {};

// Select local LLM model and auto-trigger generation if prompt is already masked
document.querySelectorAll(".model-selector button").forEach(button => {
    button.addEventListener("click", async () => {
        document.querySelectorAll(".model-selector button")
            .forEach(b => b.classList.remove("active"));

        button.classList.add("active");
        selectedModel = button.dataset.model;
        showStatus(`Selected model: ${button.textContent.trim()}`);

        // Automatically re-run generation with the newly selected model if maskedText exists
        if (maskedText) {
            await generateAlternative();
        }
    });
});

// Reusable POST helper with FastAPI error detail extraction
async function post(endpoint, body) {
    const response = await fetch(`${API}${endpoint}`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body)
    });

    const data = await response.json();

    if (!response.ok) {
        throw new Error(data.detail || "Backend request failed");
    }

    return data;
}

// Step 1: Analyze and mask sensitive PII via /api/mask
document.getElementById("analyze").addEventListener("click", async () => {
    const text = document.getElementById("prompt").value.trim();

    if (!text) {
        return showStatus("Please enter a prompt.");
    }

    const button = document.getElementById("analyze");
    button.disabled = true;
    button.textContent = "Analyzing...";

    try {
        const data = await post("/api/mask", { text });

        maskedText = data.masked_text;
        mappings = data.mappings || {};

        const items = data.detected_items || [];

        document.getElementById("warning-count").textContent =
            `Warnings: ${items.length}`;

        document.getElementById("warning-message").textContent =
            items.length
                ? `${items.length} potential privacy risks identified in this prompt.`
                : "No potential privacy risks identified.";

        document.getElementById("masked-text").textContent = maskedText;

        const detected = document.getElementById("detected-items");
        detected.replaceChildren();

        items.forEach(item => {
            const p = document.createElement("p");
            p.textContent = typeof item === "string"
                ? item
                : `${item.type}: "${item.value}" → ${item.placeholder}`;
            detected.appendChild(p);
        });

        if (!items.length) {
            detected.textContent = "No sensitive information detected.";
        }

        document.getElementById("generate").disabled = false;
        document.getElementById("response-section").classList.add("hidden");

        showStatus(`Analysis completed (${data.latency_ms} ms).`);

    } catch (error) {
        showStatus(`Error: ${error.message}`);
    } finally {
        button.disabled = false;
        button.textContent = "Analyze Prompt";
    }
});

// Toggle masked prompt & detected entity details
document.getElementById("details").addEventListener("click", () => {
    const panel = document.getElementById("details-panel");
    panel.classList.toggle("hidden");

    document.getElementById("details").textContent =
        panel.classList.contains("hidden")
            ? "Show Details"
            : "Hide Details";
});

// Step 2: Generate privacy-preserving alternative via /api/chat using selectedModel
async function generateAlternative() {
    if (!maskedText) return;

    const button = document.getElementById("generate");
    button.disabled = true;
    button.textContent = "Generating...";
    showStatus(`Generating response with ${selectedModel}...`);

    try {
        const data = await post("/api/chat", {
            masked_text: maskedText,
            model: selectedModel
        });

        // Verify actual model executed by backend (data.model_used)
        const verifiedModel = data.model_used || selectedModel;

        document.getElementById("response-text").textContent =
            data.masked_reply;

        document.getElementById("latency").textContent =
            `Model: ${verifiedModel} | Latency: ${data.latency_ms} ms`;

        document.getElementById("response-section")
            .classList.remove("hidden");

        showStatus(`Alternative generated using ${verifiedModel}.`);

    } catch (error) {
        showStatus(`Error: ${error.message}`);
    } finally {
        button.disabled = false;
        button.textContent = "Generate Alternatives";
    }
}

document.getElementById("generate").addEventListener("click", generateAlternative);

function showStatus(text) {
    document.getElementById("status").textContent = text;
}


// Close extension popup cleanly (anti-dark pattern / explicit user control)
document.getElementById("close-btn")?.addEventListener("click", () => {
    window.close();
});