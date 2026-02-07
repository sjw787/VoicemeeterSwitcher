@echo off
REM Voicemeeter API Server - Scheduled Task Version
REM This version is designed to run as a Windows scheduled task

cd /d "%~dp0"

REM Activate virtual environment
call .venv\Scripts\activate.bat

REM Run without --reload (more stable for scheduled tasks)
REM Use --host 0.0.0.0 for network access
uvicorn api:app --host 0.0.0.0 --port 8080
