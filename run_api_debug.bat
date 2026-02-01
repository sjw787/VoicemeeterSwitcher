@echo off
REM Start API with visible console window for debugging
echo Starting Voicemeeter API with visible logs...
echo.
cd /d "%~dp0"
call .venv\Scripts\activate.bat
echo API is starting - leave this window open to see logs
echo Press Ctrl+C to stop the API
echo.
uvicorn api:app --host 0.0.0.0 --port 5000
pause
