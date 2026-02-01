# Stop the Voicemeeter API running in background

Write-Host "Stopping Voicemeeter API..."

# Find and kill uvicorn processes
$processes = Get-Process -Name "uvicorn" -ErrorAction SilentlyContinue

if ($processes) {
    foreach ($proc in $processes) {
        Stop-Process -Id $proc.Id -Force
        Write-Host "✓ Stopped API (PID: $($proc.Id))"
    }
} else {
    Write-Host "No running API found"
}

Write-Host ""
Write-Host "API stopped"
