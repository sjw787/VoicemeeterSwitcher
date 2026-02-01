@echo off
echo ==========================================
echo Starting Voicemeeter Control System
echo ==========================================
echo.
echo Starting API Server...
start "Voicemeeter API" cmd /k "cd /d %~dp0 && run_api.bat"
echo Waiting 5 seconds for API to start...
timeout /t 5 /nobreak >nul
echo.
echo Starting Web UI...
start "Voicemeeter Web UI" cmd /k "cd /d %~dp0 && run_webui.bat"
echo.
echo ==========================================
echo Both servers are starting!
echo.
echo API Server: http://localhost:5000
echo Web UI: http://localhost:3000
echo.
echo Press any key to close this window...
echo (The servers will continue running in their own windows)
echo ==========================================
pause >nul
