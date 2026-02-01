# 🎉 Voicemeeter API - Background Mode Setup Complete!

## ✅ What I've Done

I've set up the Voicemeeter API to run **completely in the background** with no visible windows.

## 📁 Files Created

### Control Scripts

1. **`start_api_background.ps1`** - Starts the API hidden in background
2. **`stop_api.ps1`** - Stops the API
3. **`check_api_status.ps1`** - Check if API is running
4. **`setup_background_autostart.ps1`** - Configure auto-start at login

### Configuration

5. **`run_api_hidden.bat`** - Alternative batch file for hidden start
6. **Scheduled Task** - "VoicemeeterAPI" task in Windows Task Scheduler

## 🚀 How to Use

### Start the API Now (in background)
```powershell
.\start_api_background.ps1
```

### Check if it's Running
```powershell
.\check_api_status.ps1
```

### Stop the API
```powershell
.\stop_api.ps1
```

## 🔄 Auto-Start Configuration

The API is now configured to **start automatically** when you log in:
- ✅ Runs in background (no window)
- ✅ Starts at login
- ✅ Runs with your user privileges
- ✅ Survives restarts

## 🎯 Testing

### Test 1: Check Status
```powershell
.\check_api_status.ps1
```

Should show:
```
✓ Voicemeeter API is running
  Process ID: XXXX
  Access at: http://localhost:5000
  Status: Responding ✓
```

### Test 2: Access from Browser
Open: http://localhost:5000

Should show:
```json
{
  "name": "Voicemeeter Control API",
  "version": "1.0",
  "endpoints": [...]
}
```

### Test 3: Web UI
Open: http://localhost:3000

Should be able to switch profiles!

## 📊 Task Scheduler Details

The scheduled task:
- **Name:** VoicemeeterAPI
- **Trigger:** At log on (your user)
- **Action:** Start API in background
- **No console window**
- **Runs even if on battery**

To view in Task Scheduler:
1. Press `Win+R`
2. Type: `taskschd.msc`
3. Look for "VoicemeeterAPI"

## 🛠️ Management Commands

### Check Status
```powershell
.\check_api_status.ps1
```
No more manual starting - it just works! 🚀

**Next time you log in, the API will start automatically in the background!** 🎉

- ✅ Integrated with the web UI
- ✅ Easy to manage with PowerShell scripts
- ✅ Accessible from any device on your network
- ✅ Starts automatically at login
- ✅ Runs in the background (no visible window)
Your Voicemeeter API now:

## ✅ Summary

| `Unregister-ScheduledTask -TaskName "VoicemeeterAPI"` | Remove auto-start |
| `Get-ScheduledTask -TaskName "VoicemeeterAPI"` | View scheduled task |
| `.\setup_background_autostart.ps1` | Configure auto-start |
| `.\check_api_status.ps1` | Check if running |
| `.\stop_api.ps1` | Stop API |
| `.\start_api_background.ps1` | Start API in background |
|---------|---------|
| Command | Purpose |

## 📝 Quick Reference

- Everything works seamlessly
- Just open http://localhost:3000
- No need to manually start the API anymore
The web UI will automatically connect to the background API:

## 🎨 Integration with Web UI

```
Get-Process -Name "uvicorn" | Stop-Process -Force
```powershell
**Force kill:**

### Process Won't Stop?

3. Click the "History" tab
2. Find "VoicemeeterAPI"
1. Open Task Scheduler (`taskschd.msc`)
**Check task history:**

```
Start-ScheduledTask -TaskName "VoicemeeterAPI"
```powershell
**Run it manually:**

```
Get-ScheduledTask -TaskName "VoicemeeterAPI"
```powershell
**Check the task:**

### Auto-Start Not Working?

Look for error messages.
```
.\run_api.bat
```powershell
**Check 3:** Try starting with console visible

```
netstat -ano | findstr :5000
```powershell
**Check 2:** Check for port conflicts

```
Get-Process -Name "voicemeeter8" -ErrorAction SilentlyContinue
```powershell
**Check 1:** Is Voicemeeter running?

### API Not Starting?

## 🔍 Troubleshooting

```
.\setup_background_autostart.ps1
```powershell
### Re-enable Auto-Start

```
Unregister-ScheduledTask -TaskName "VoicemeeterAPI" -Confirm:$false
```powershell
### Disable Auto-Start

```
.\start_api_background.ps1
Start-Sleep -Seconds 2
.\stop_api.ps1
```powershell
### Restart

```
.\stop_api.ps1
```powershell
### Stop

```
.\start_api_background.ps1
```powershell
### Start Manually

