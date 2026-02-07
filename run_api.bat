@echo off
REM Voicemeeter API Server
cd /d "%~dp0"
call .venv\Scripts\activate.bat
echo Starting Voicemeeter Control API on http://localhost:8080
uvicorn api:app --host 0.0.0.0 --port 8080 --reload
