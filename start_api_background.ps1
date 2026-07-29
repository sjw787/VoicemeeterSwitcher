# Start Voicemeeter API in background (completely hidden)

$scriptPath = Split-Path -Parent $MyInvocation.MyCommand.Path
$pythonExe = Join-Path $scriptPath ".venv\Scripts\python.exe"
$uvicornExe = Join-Path $scriptPath ".venv\Scripts\uvicorn.exe"

# Start the process hidden in the background
$processInfo = New-Object System.Diagnostics.ProcessStartInfo
$processInfo.FileName = $uvicornExe
$processInfo.Arguments = "api:app --host 0.0.0.0 --port 8080"
$processInfo.WorkingDirectory = $scriptPath
$processInfo.UseShellExecute = $false
$processInfo.CreateNoWindow = $true
$processInfo.WindowStyle = [System.Diagnostics.ProcessWindowStyle]::Hidden

$process = [System.Diagnostics.Process]::Start($processInfo)

Write-Host "✓ Voicemeeter API started in background (PID: $($process.Id))"
Write-Host "  Access at: http://localhost:8080"
Write-Host ""
Write-Host "To stop the API, run: stop_api.ps1"
