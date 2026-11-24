@echo off
title Local AI Privacy Protector - Backend Launcher
echo ========================================================
echo   Starting Local AI Privacy Protector Backend...
echo ========================================================

:: 1. Check/Create Virtual Environment
if not exist ".venv" (
    echo [1/4] Creating Python virtual environment...
    python -m venv .venv
)

:: 2. Activate Virtual Environment & Install Dependencies
echo [2/4] Activating environment and checking dependencies...
call .venv\Scripts\activate
pip install -q -r backend\requirements.txt
python -m spacy download en_core_web_sm >nul 2>&1

:: 3. Check Ollama & Pull Default Model
echo [3/4] Checking Ollama and default model (mistral)...
where ollama >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Ollama is not installed. Please install it from https://ollama.com
    pause
    exit /b 1
)
start "" /B ollama serve >nul 2>&1
timeout /t 2 /nobreak >nul
ollama pull mistral

:: 4. Start FastAPI Server
echo [4/4] Launching Local FastAPI Server at http://localhost:8000 ...
echo Keep this window open while using the Chrome Extension.
echo ========================================================
cd backend
uvicorn main:app --host 127.0.0.1 --port 8000
pause
