@echo off
setlocal enabledelayedexpansion

echo ==========================================
echo Quick Network Setup
echo ==========================================
echo.

echo Detecting your network information...
for /f "tokens=*" %%a in ('hostname') do set COMPUTERNAME=%%a
for /f "tokens=2 delims=:" %%a in ('ipconfig ^| findstr /c:"IPv4 Address"') do (
    set IP=%%a
    set IP=!IP: =!
    goto :found_ip
)
:found_ip

echo.
echo Computer Name: %COMPUTERNAME%
echo IP Address: %IP%
echo.

echo Updating .env.local file...
(
echo # API URL for network access
echo NEXT_PUBLIC_API_URL=http://%COMPUTERNAME%:5000
echo.
echo # Alternative: Use IP address if computer name doesn't work
echo # NEXT_PUBLIC_API_URL=http://%IP%:5000
) > voicemeeter-web-ui\.env.local

echo   ✓ Updated .env.local
echo.

echo ==========================================
echo Setup Complete!
echo ==========================================
echo.
echo From other devices, access the web UI at:
echo.
echo   Option 1: http://%COMPUTERNAME%.local:3000
echo   Option 2: http://%IP%:3000
echo.
echo IMPORTANT: Restart the web UI server now!
echo   1. Stop the current web UI (Ctrl+C)
echo   2. Run: run_webui.bat
echo.
pause
