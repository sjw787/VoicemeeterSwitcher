@echo off
echo Starting Voicemeeter Web UI...
cd /d "%~dp0voicemeeter-web-ui"
call npm run dev
pause
