@echo off
echo Testing Voicemeeter API...
echo.

echo [1] Testing API connection...
curl -s http://localhost:5000/
echo.
echo.

echo [2] Getting available profiles...
curl -s http://localhost:5000/api/profiles
echo.
echo.

echo [3] Getting current status...
curl -s http://localhost:5000/api/status
echo.
echo.

echo Done! Check output above for any errors.
echo.
echo If you see errors:
echo - Make sure Voicemeeter is running
echo - Make sure API server is running (run_api.bat)
echo - Check that profiles exist in settings folder
echo.
pause
