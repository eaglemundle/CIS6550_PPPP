
const API = "http://127.0.0.1:8000";

let selectedModel = "llama3.2:3b";
let maskedText = "";
let mappings = {};

// Select model
document.querySelectorAll(".model-selector button").forEach(button => {
    button.addEventListener("click", () => {
        document.querySelectorAll(".model-selector button")
            .forEach(b => b.classList.remove("active"));

        button.classList.add("active");
        selectedModel = button.dataset.model;
    });
});

// API helper
async function post(endpoint, body) {
    const response = await fetch(`${API}${endpoint}`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body)
    });

    const data = await response.json();

    if (!response.ok) {
        throw new Error(data.detail || "Request failed");
    }

    return data;
}

// Analyze and mask prompt
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
                : item.type || item.label || "Sensitive information detected";
            detected.appendChild(p);
        });

        if (!items.length) {
            detected.textContent = "No sensitive information detected.";
        }

        document.getElementById("generate").disabled = false;
        document.getElementById("response-section").classList.add("hidden");

        showStatus("Prompt analysis completed.");

    } catch (error) {
        showStatus(error.message);
    } finally {
        button.disabled = false;
        button.textContent = "Analyze Prompt";
    }
});

// Show / hide details
document.getElementById("details").addEventListener("click", () => {
    const panel = document.getElementById("details-panel");
    panel.classList.toggle("hidden");

    document.getElementById("details").textContent =
        panel.classList.contains("hidden")
            ? "Show Details"
            : "Hide Details";
});

// Generate alternative using selected local model
document.getElementById("generate").addEventListener("click", async () => {
    if (!maskedText) return;

    const button = document.getElementById("generate");
    button.disabled = true;
    button.textContent = "Generating...";

    try {
        const data = await post("/api/chat", {
            masked_text: maskedText,
            model: selectedModel
        });

        document.getElementById("response-text").textContent =
            data.masked_reply;

        document.getElementById("latency").textContent =
            `Model: ${selectedModel} | Latency: ${data.latency_ms} ms`;

        document.getElementById("response-section")
            .classList.remove("hidden");

        showStatus("Alternative generated successfully.");

    } catch (error) {
        showStatus(error.message);
    } finally {
        button.disabled = false;
        button.textContent = "Generate Alternatives";
    }
});

function showStatus(text) {
    document.getElementById("status").textContent = text;
}
