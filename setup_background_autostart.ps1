# Setup Voicemeeter API to run at startup (background)

$scriptPath = Split-Path -Parent $MyInvocation.MyCommand.Path
$startupScript = Join-Path $scriptPath "start_api_background.ps1"

# Create a scheduled task to run at logon
$action = New-ScheduledTaskAction -Execute "powershell.exe" -Argument "-WindowStyle Hidden -ExecutionPolicy Bypass -File `"$startupScript`""
$trigger = New-ScheduledTaskTrigger -AtLogOn -User $env:USERNAME
$settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -StartWhenAvailable
$principal = New-ScheduledTaskPrincipal -UserId $env:USERNAME -RunLevel Highest

# Remove existing task if it exists
Unregister-ScheduledTask -TaskName "VoicemeeterAPI" -Confirm:$false -ErrorAction SilentlyContinue

# Register the new task
Register-ScheduledTask -TaskName "VoicemeeterAPI" -Action $action -Trigger $trigger -Settings $settings -Principal $principal

Write-Host ""
Write-Host "✓ Voicemeeter API configured to start at login!" -ForegroundColor Green
Write-Host ""
Write-Host "The API will now start automatically in the background when you log in."
Write-Host "No console window will appear."
Write-Host ""
Write-Host "To start it now, run: .\start_api_background.ps1"
Write-Host "To check status, run: .\check_api_status.ps1"
Write-Host "To stop it, run: .\stop_api.ps1"
Write-Host ""
Write-Host "To remove auto-start:"
Write-Host "  Unregister-ScheduledTask -TaskName 'VoicemeeterAPI'"
Write-Host ""
