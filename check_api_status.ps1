# Check if Voicemeeter API is running
$processes = Get-Process -Name "uvicorn" -ErrorAction SilentlyContinue
if ($processes) {
    Write-Host "Voicemeeter API is running" -ForegroundColor Green
    Write-Host ""
    foreach ($proc in $processes) {
        Write-Host "  Process ID: $($proc.Id)"
        Write-Host "  CPU Time: $($proc.CPU)"
        Write-Host "  Memory: $([math]::Round($proc.WorkingSet64 / 1MB, 2)) MB"
    }
    Write-Host ""
    Write-Host "  Access at: http://localhost:5000"
    # Test if responding
    try {
        $response = Invoke-WebRequest -Uri "http://localhost:5000" -UseBasicParsing -TimeoutSec 2
        Write-Host "  Status: Responding" -ForegroundColor Green
    } catch {
        Write-Host "  Status: Not responding" -ForegroundColor Yellow
    }
} else {
    Write-Host "Voicemeeter API is not running" -ForegroundColor Red
    Write-Host ""
    Write-Host "To start it in background, run: .\start_api_background.ps1"
}
Write-Host ""
