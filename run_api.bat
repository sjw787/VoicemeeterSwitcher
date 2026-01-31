@echo off
REM Voicemeeter API Server
cd /d "%~dp0"
call .venv\Scripts\activate.bat
uvicorn api:app --host 0.0.0.0 --port 5000 --reload
