@echo off
echo ==========================================
echo Voicemeeter Setup Verification
echo ==========================================
echo.

echo [1/5] Checking Python virtual environment...
if exist ".venv\Scripts\python.exe" (
    echo ✓ Virtual environment found
) else (
    echo ✗ Virtual environment NOT found
    echo   Run: python -m venv .venv
)
echo.

echo [2/5] Checking required Python packages...
.venv\Scripts\python.exe -c "import fastapi; import voicemeeterlib" 2>nul
if %ERRORLEVEL% EQU 0 (
    echo ✓ Python packages installed
) else (
    echo ✗ Python packages NOT installed
    echo   Run: .venv\Scripts\pip install fastapi uvicorn voicemeeterlib
)
echo.

echo [3/5] Checking settings folder...
if exist "settings\" (
    echo ✓ Settings folder exists
    set count=0
    for %%F in (settings\*.xml) do set /a count+=1
    if !count! GTR 0 (
        echo ✓ Found !count! XML profile(s)
    ) else (
        echo ⚠ No XML profiles found in settings folder
    )
) else (
    echo ✗ Settings folder NOT found
    echo   Create it: mkdir settings
)
echo.

echo [4/5] Checking Web UI folder...
if exist "voicemeeter-web-ui\" (
    echo ✓ Web UI folder exists
    if exist "voicemeeter-web-ui\node_modules\" (
        echo ✓ Node modules installed
    ) else (
        echo ⚠ Node modules NOT installed
        echo   Run: cd voicemeeter-web-ui && npm install
    )
) else (
    echo ✗ Web UI folder NOT found
)
echo.

echo [5/5] Checking batch files...
if exist "run_api.bat" (echo ✓ run_api.bat) else (echo ✗ run_api.bat)
if exist "run_webui.bat" (echo ✓ run_webui.bat) else (echo ✗ run_webui.bat)
if exist "start_all.bat" (echo ✓ start_all.bat) else (echo ✗ start_all.bat)
echo.

echo ==========================================
echo Verification Complete!
echo ==========================================
echo.
echo To start using the system:
echo   1. Double-click: start_all.bat
echo   2. Open browser: http://localhost:3000
echo.
echo For more info, see:
echo   - README.md
echo   - WEB_UI_GUIDE.md
echo   - SETUP_COMPLETE.md
echo.
pause
