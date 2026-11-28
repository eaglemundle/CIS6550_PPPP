
# Local AI Privacy Protector

**A Local-First AI Prompt Privacy Protection System Using Chrome Extensions and On-Device LLMs.**    

**Category of Topic :** Data Mining and Artificial Intelligence Approaches.


## Description

Local AI Privacy Protector is a privacy-focused Chrome extension designed to detect and protect sensitive information in AI prompts before processing.

The system uses Personally Identifiable Information (PII) detection and automated prompt masking to identify sensitive data, such as names, email addresses, and phone numbers. It replaces detected information with placeholders and processes the sanitized prompts using a locally hosted Large Language Model (LLM) through Ollama.

By keeping prompt processing and AI inference on the user's device, the project aims to reduce sensitive data exposure to external AI services and improve user control over personal information.

## Project Timeline

| Phase | Activities |Timeline
|---|---|---|
| Design | Privacy assessment and system architecture | Oct 20 ~ Nov 6 |
| Development | Chrome extension, PII detection, and Ollama integration | Nov 7 ~ Nov 20 |
| Testing | Detection accuracy and network verification | Nov 20 ~ Nov 28 |
| Evaluation | Performance, response quality, and usability | Nov 29 ~ Dec 4 |
| Finalization | DOCUMENTATION (50% of total grade) - methodology, implemetation details, evaluation metrics, limitations, DISCISSIONS, and future steps | Dec 5 ~ Dec 10|

## Key Features

- **PII Detection:** Identify sensitive information using regular expressions and/or Microsoft Presidio.
- **Automatic Prompt Masking:** Replace detected sensitive information with unique placeholders.
- **User Privacy Controls:** Allow users to review and manage detected information.
- **Local AI Processing:** Generate responses using locally hosted LLMs through Ollama.
- **Response Restoration:** Restore original information in AI-generated responses when appropriate.
- **Privacy Protection:** Minimize external data transmission through local-first processing.

## Technology Stack

| Component | Technology |
|---|---|
| Browser Extension | Chrome Extension Manifest V3 |
| Frontend | HTML, CSS, JavaScript |
| Backend | Python, FastAPI |
| PII Detection | Regex, Microsoft Presidio |
| AI Runtime | Ollama |
| Local LLM | llama3.2:3b, mistral, qwen2.5:3b |
| Testing | Python, Chrome DevTools, Wireshark |
| Version Control | Git, GitHub |

## Prototype

**Figma:** [Insert Figma Prototype Link]

**Screenshots:** [Insert Screenshots or Demo GIF]

## System Architecture

```mermaid
flowchart TB
    classDef client fill:#e8f1fa,stroke:#2b6cb0,stroke-width:2px,color:#1a202c
    classDef backend fill:#ebf8ff,stroke:#3182ce,stroke-width:2px,color:#1a202c
    classDef llm fill:#e6fffa,stroke:#2c7a7b,stroke-width:2px,color:#1a202c
    classDef eval fill:#edf2f7,stroke:#4a5568,stroke-width:2px,color:#1a202c
    classDef storage fill:#f7fafc,stroke:#718096,stroke-width:1.5px,stroke-dasharray: 4 4,color:#1a202c

    subgraph Runtime["Runtime Privacy Guard Pipeline (127.0.0.1 Localhost - Zero External Leakage)"]
        direction LR
        subgraph Ext["Chrome Extension (Manifest V3)"]
            UI["Content Script & Popup UI<br/>• Dismiss Button (×)<br/>• Entity Review & Model Select"]:::client
            Storage["Chrome Local Storage<br/>Ephemeral Placeholder Mappings<br/>(<ID> ↔ Original PII)"]:::storage
            UI <-->|"Store / Lookup"| Storage
        end

        subgraph API["FastAPI Backend (:8000)"]
            Orch["API Orchestrator<br/>Request Routing & Session Context"]:::backend
            Presidio["Presidio NER + Custom Canadian Regex<br/>Canadian SIN, Postal Codes, PHI, Secrets<br/>Avg Masking Latency: ~8.30 ms"]:::backend
            Orch <-->|"2. Detect & Mask"| Presidio
        end

        subgraph Ollama["Ollama Local Runtime (:11434)"]
            Engine["Local Inference Engine<br/>Llama 3.2 | Qwen 2.5 | Mistral<br/>100% Offline Inference"]:::llm
        end

        UI -->|"1. Raw User Prompt"| Orch
        Orch -->|"3. Masked Prompt<br/>(<CA_SIN_1>, <PERSON_1>)"| Engine
        Engine -->|"4. Masked Output"| Orch
        Orch -->|"5. Rehydrated Response<br/>(Original PII Restored)"| UI
    end

    subgraph Offline["Offline Benchmark & Validation Pipeline (Backend Evaluation)"]
        direction LR
        Gen["Synthetic Dataset Generator<br/>generate_3000_edge_heavy.py<br/>3,000 Prompts / 4,750 Entities (Seed 42)<br/>40% Baseline + 60% Edge Cases"]:::eval
        Runner["Evaluation Runner<br/>evaluate.py & benchmark_models.py<br/>Accuracy, Latency & Model Comparison"]:::eval
        Metrics["Empirical Metrics & Audit<br/>• Detection: 8.30 ms | 74.34% Recall | 67.26% F1<br/>• LLM Integrity: Leak & Restoration Rates<br/>• Network Isolation: DevTools 127.0.0.1 Audit"]:::eval
        Gen -->|"Runs 3,000-Prompt Suite"| Runner
        Runner -->|"Aggregates Results"| Metrics
    end

    Runner -.->|"Test Batch (/api/mask, /api/chat)"| Orch
```

All prompt processing and AI inference are intended to remain on the local machine without requiring external AI APIs.

## System Architecture

```text
User Prompt
    |
Chrome Extension
    |
PII Detection
    |
Prompt Masking
    |
Local FastAPI Backend
    |
Ollama - Local LLM
    |
AI Response
    |
Response Restoration
    |
   User   
```

All prompt processing and AI inference are intended to remain on the local machine without requiring external AI APIs.

## Project Structure
```text
CIS6550_PPPP/
├── extension-FE/               # Chrome Extension (Manifest V3 Frontend)
│   ├── manifest.json           # Extension permissions & popup configuration
│   ├── popup.html              # Popup UI layout with top-level model selector
│   ├── popup.css               # Readable dark-mode styling (760px width)
│   └── popup.js                # FastAPI integration & auto-regeneration logic
│
├── backend/                    # Local-First FastAPI & Presidio Inference Server
│   ├── main.py                 # API endpoints (/api/mask, /api/chat, /api/restore)
│   ├── pii_config.py           # Custom regex rules, medical deny-lists, & allow-lists
│   ├── models.json             # Externalized Ollama model configuration
│   ├── benchmark_models.py     # Multi-model latency & token integrity benchmark
│   ├── evaluate.py             # PII detection precision/recall evaluation
│   └── requirements.txt        # Python dependencies
│
├── test/                       # Unit & Integration Tests
│   ├── test_pii.py             # Presidio & regex entity detection tests
│   └── test_masking.py         # Placeholder substitution & restoration tests
│
├── start.bat                   # One-click Windows launcher (zero-access-log mode)
├── README.md                   # Setup instructions, architecture overview, & Ollama guide
├── .gitignore                  # Git ignore rules (.venv, __pycache__, local logs)
└── Final_report.pdf            # CIS6550 Capstone Final Report
```


## Installation and Setup

### 1. Clone the Repository

```bash
git clone https://github.com/YOUR-USERNAME/Local-AI-Privacy-Protector.git

cd Local-AI-Privacy-Protector
```

### 2. Set Up the Python Environment

```bash
python -m venv .venv
```

Activate the environment:

**Windows:**
```powershell
.venv\Scripts\activate
```

**macOS / Linux:**
```bash
source .venv/bin/activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Install Ollama

Download Ollama:

https://ollama.com/

Download a supported local model:

```bash
ollama pull llama3.2:3b
```

Start the Ollama service and verify that the model is available.

### 5. Start the Local Backend

```bash
uvicorn main:app --reload --host 127.0.0.1 --port 8000
```

### 6. Load the Chrome Extension

1. Open Google Chrome.
2. Navigate to `chrome://extensions`.
3. Enable **Developer mode**.
4. Select **Load unpacked**.
5. Select the `extension/` directory.
6. Open the extension and start testing.
  

## Testing and Evaluation

The prototype will be evaluated using synthetic prompts containing different categories of sensitive information.

| Evaluation Area | Measurement |
|---|---|
| PII Detection | Precision, Recall, F1-score |
| Privacy Protection | External network transmission |
| Performance | Processing and inference latency |
| Response Quality | Usefulness of masked-prompt responses |
| Usability | Ease of use and clarity of privacy controls |


## Privacy and Security Considerations



**Note:** Local processing reduces exposure to external services but does not automatically guarantee complete security or legal compliance.


