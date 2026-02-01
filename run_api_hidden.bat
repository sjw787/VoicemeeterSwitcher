@echo off
REM Start Voicemeeter API in background (hidden window)

REM Get the directory where this script is located
cd /d "%~dp0"

REM Start the API in a hidden window using PowerShell
powershell -WindowStyle Hidden -Command "& { cd '%~dp0'; .\.venv\Scripts\activate.bat; uvicorn api:app --host 0.0.0.0 --port 5000 }"
