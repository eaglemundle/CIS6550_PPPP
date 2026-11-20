from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import requests

app = FastAPI(title="Local AI Privacy Protector API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

OLLAMA_URL = "http://127.0.0"
MODEL_NAME = "llama3.2:3b"

class PromptRequest(BaseModel):
    text: str

class PromptResponse(BaseModel):
    reply: str

@app.get("/")
def health_check():
    return {"status": "ok", "model": MODEL_NAME}

@app.post("/api/analyze", response_model=PromptResponse)
def analyze_text(request: PromptRequest):
    system_instruction = (
        "You are a privacy protection assistant. Analyze the following text "
        "for any sensitive personal information (PII) and provide a safe response:\n\n"
    )
    payload = {
        "model": MODEL_NAME,
        "prompt": system_instruction + request.text,
        "stream": False
    }

    try:
        response = requests.post(OLLAMA_URL, json=payload, timeout=30)
        response.raise_for_status()
        return PromptResponse(reply=response.json().get("response", ""))
    except requests.exceptions.ConnectionError:
        raise HTTPException(status_code=503, detail="Ollama service is unavailable.")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
