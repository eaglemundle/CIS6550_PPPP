from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Optional
from presidio_analyzer import AnalyzerEngine, PatternRecognizer, Pattern
from presidio_analyzer.nlp_engine import NlpEngineProvider
import requests
import time

from pii_config import (
    OLLAMA_URL,
    DEFAULT_MODEL,
    SUPPORTED_MODELS,
    REGEX_RULES,
    MEDICAL_DENY_LIST,
    MEDICAL_CONTEXT_WORDS,
    HIGH_RISK_ENTITIES,
    ALLOW_LIST,
)

app = FastAPI(title="Local AI Privacy Protector API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize Presidio with lightweight spaCy model
nlp_config = {
    "nlp_engine_name": "spacy",
    "models": [{"lang_code": "en", "model_name": "en_core_web_sm"}],
}
provider = NlpEngineProvider(nlp_configuration=nlp_config)
analyzer = AnalyzerEngine(nlp_engine=provider.create_engine())

# Dynamically load custom Regex rules from pii_config.py
grouped_patterns: Dict[str, List[Pattern]] = {}
for entity_type, name, regex, score in REGEX_RULES:
    grouped_patterns.setdefault(entity_type, []).append(
        Pattern(name=name, regex=regex, score=score)
    )

for entity_type, patterns in grouped_patterns.items():
    analyzer.registry.add_recognizer(
        PatternRecognizer(supported_entity=entity_type, patterns=patterns)
    )

# Load Medical Deny-List recognizer
analyzer.registry.add_recognizer(
    PatternRecognizer(
        supported_entity="MEDICAL_INFO",
        deny_list=MEDICAL_DENY_LIST,
        context=MEDICAL_CONTEXT_WORDS
    )
)

class MaskRequest(BaseModel):
    text: str

class DetectedItem(BaseModel):
    type: str
    value: str
    placeholder: str
    score: float

class MaskResponse(BaseModel):
    risk_level: str
    masked_text: str
    mappings: Dict[str, str]
    detected_items: List[DetectedItem]
    latency_ms: float

class ChatRequest(BaseModel):
    masked_text: str
    model: Optional[str] = DEFAULT_MODEL

class ChatResponse(BaseModel):
    model_used: str
    masked_reply: str
    latency_ms: float

class RestoreRequest(BaseModel):
    text: str
    mappings: Dict[str, str]

class RestoreResponse(BaseModel):
    restored_text: str

@app.get("/")
def health_check():
    return {
        "status": "ok",
        "default_model": DEFAULT_MODEL,
        "supported_models": SUPPORTED_MODELS
    }

@app.post("/api/mask", response_model=MaskResponse)
def mask_prompt(request: MaskRequest):
    start_time = time.perf_counter()
    text = request.text

    results = analyzer.analyze(
        text=text,
        language="en",
        score_threshold=0.6,
        allow_list=ALLOW_LIST
    )

    results = sorted(results, key=lambda x: (x.score, x.end - x.start), reverse=True)

    filtered_results = []
    for res in results:
        if not any(res.start < prev.end and res.end > prev.start for prev in filtered_results):
            filtered_results.append(res)

    filtered_results = sorted(filtered_results, key=lambda x: x.start)

    entity_counts: Dict[str, int] = {}
    mappings: Dict[str, str] = {}
    detected_items: List[DetectedItem] = []

    masked_text = text
    offset_shift = 0

    for res in filtered_results:
        original_val = text[res.start:res.end]
        entity_type = res.entity_type

        entity_counts[entity_type] = entity_counts.get(entity_type, 0) + 1
        placeholder = f"[{entity_type}_{entity_counts[entity_type]}]"

        mappings[placeholder] = original_val
        detected_items.append(
            DetectedItem(
                type=entity_type,
                value=original_val,
                placeholder=placeholder,
                score=round(res.score, 2)
            )
        )

        adj_start = res.start + offset_shift
        adj_end = res.end + offset_shift
        masked_text = masked_text[:adj_start] + placeholder + masked_text[adj_end:]
        offset_shift += len(placeholder) - (res.end - res.start)

    if not detected_items:
        risk_level = "LOW"
    elif any(item.type in HIGH_RISK_ENTITIES for item in detected_items) or len(detected_items) >= 3:
        risk_level = "HIGH"
    else:
        risk_level = "MEDIUM"

    latency_ms = round((time.perf_counter() - start_time) * 1000, 2)

    return MaskResponse(
        risk_level=risk_level,
        masked_text=masked_text,
        mappings=mappings,
        detected_items=detected_items,
        latency_ms=latency_ms
    )

@app.post("/api/chat", response_model=ChatResponse)
def chat_with_local_llm(request: ChatRequest):
    start_time = time.perf_counter()
    selected_model = request.model if request.model in SUPPORTED_MODELS else DEFAULT_MODEL

    system_instruction = (
        "You are a helpful AI assistant. The user's prompt contains privacy placeholders "
        "such as [PERSON_1], [API_KEY_1], [MEDICAL_INFO_1], [SOURCE_CODE_1], etc. "
        "Keep these exact placeholders intact in your response where appropriate so the client can restore them later.\n\n"
        f"User Prompt:\n{request.masked_text}"
    )

    payload = {
        "model": selected_model,
        "prompt": system_instruction,
        "stream": False
    }

    try:
        response = requests.post(OLLAMA_URL, json=payload, timeout=90)
        response.raise_for_status()
        reply = response.json().get("response", "")
        latency_ms = round((time.perf_counter() - start_time) * 1000, 2)
        return ChatResponse(
            model_used=selected_model,
            masked_reply=reply,
            latency_ms=latency_ms
        )
    except requests.exceptions.ConnectionError:
        raise HTTPException(status_code=503, detail="Ollama service is unavailable.")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/restore", response_model=RestoreResponse)
def restore_response(request: RestoreRequest):
    restored = request.text
    for placeholder, original_val in request.mappings.items():
        restored = restored.replace(placeholder, original_val)
    return RestoreResponse(restored_text=restored)
