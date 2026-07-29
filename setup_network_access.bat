@echo off
echo ==========================================
echo Network Access Setup
echo ==========================================
echo.

echo [1/3] Getting your network information...
echo.
echo Your Computer Name:
hostname
echo.
echo Your IP Address(es):
ipconfig | findstr IPv4
echo.

echo [2/3] Adding firewall rules...
netsh advfirewall firewall delete rule name="Voicemeeter Web UI" >nul 2>&1
netsh advfirewall firewall delete rule name="Voicemeeter API" >nul 2>&1
netsh advfirewall firewall add rule name="Voicemeeter Web UI" dir=in action=allow protocol=TCP localport=3100 >nul
netsh advfirewall firewall add rule name="Voicemeeter API" dir=in action=allow protocol=TCP localport=8080 >nul
echo   + Port 3100 (Web UI) - OK
echo   + Port 8080 (API) - OK
echo.

echo [3/3] Next steps:
echo.
echo   1. Note your computer name or IP address above
echo.
echo   2. Edit this file:
echo      voicemeeter-web-ui\.env.local
echo.
echo   3. Change this line:
echo      NEXT_PUBLIC_API_URL=http://localhost:8080
echo.
echo   4. To this (using your computer name):
echo      NEXT_PUBLIC_API_URL=http://YOUR-COMPUTER-NAME:8080
echo.
echo   5. Or this (using your IP):
echo      NEXT_PUBLIC_API_URL=http://YOUR-IP-ADDRESS:8080
echo.
echo   6. Restart the web UI server (run_webui.bat)
echo.
echo   7. Access from other devices:
echo      http://YOUR-COMPUTER-NAME.local:3100
echo      or
echo      http://YOUR-IP-ADDRESS:3100
echo.
echo ==========================================
pause
