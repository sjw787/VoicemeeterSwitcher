# Quick Setup: Auto-start Voicemeeter API

$WshShell = New-Object -ComObject WScript.Shell
$Startup = [System.Environment]::GetFolderPath('Startup')
$Shortcut = $WshShell.CreateShortcut("$Startup\Voicemeeter API.lnk")
$Shortcut.TargetPath = "$PSScriptRoot\run_api.bat"
$Shortcut.WorkingDirectory = $PSScriptRoot
$Shortcut.WindowStyle = 7  # Minimized
$Shortcut.Description = "Voicemeeter API Server"
$Shortcut.Save()

Write-Host ""
Write-Host "✓ Auto-start setup complete!" -ForegroundColor Green
Write-Host ""
Write-Host "The Voicemeeter API will now start automatically when you log in."
Write-Host "It will run minimized in the background."
Write-Host ""
Write-Host "To test it now, run: .\run_api.bat"
Write-Host ""
Write-Host "To remove auto-start, delete this shortcut:"
Write-Host "  $Startup\Voicemeeter API.lnk"
Write-Host ""
