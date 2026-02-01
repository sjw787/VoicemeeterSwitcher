# Running Voicemeeter API as a Scheduled Task
Save as `setup_autostart.ps1` and run it!

```
Write-Host "The API will now start automatically when you log in!"
Write-Host "✓ Created startup shortcut for Voicemeeter API"

$Shortcut.Save()
$Shortcut.WindowStyle = 7  # 7 = Minimized
$Shortcut.WorkingDirectory = "C:\Users\Sam\PycharmProjects\VoicemeeterSwitcher"
$Shortcut.TargetPath = "C:\Users\Sam\PycharmProjects\VoicemeeterSwitcher\run_api.bat"
$Shortcut = $WshShell.CreateShortcut("$Startup\Voicemeeter API.lnk")
$Startup = [System.Environment]::GetFolderPath('Startup')
$WshShell = New-Object -ComObject WScript.Shell
# Create shortcut in startup folder
```powershell

Run this PowerShell script:

## Quick Setup - Startup Folder Method

- ✅ Runs even when not logged in (if Voicemeeter also runs as service)
- ✅ Automatic recovery
- ✅ True background service
**For advanced users:** Use **Option 3** (Windows Service)

- ✅ Can see console for debugging
- ✅ Easy to stop/restart
- ✅ Runs in correct session
- ✅ Simple to set up
**For most users:** Use **Option 1** (Startup folder)

## Recommended Setup

```
uvicorn api:app --host 0.0.0.0 --port 5000 > api_log.txt 2>&1
```batch
**Option B:** Add logging to the batch file

```
.\run_api_task.bat
```powershell
**Option A:** Run manually first

When running as a task, you won't see the console. To debug:

### Can't see console output

```
.\run_api_task.bat
cd C:\Users\Sam\PycharmProjects\VoicemeeterSwitcher
```powershell
**Check 3:** Run manually to see errors

2. Check the **Last Run Result** column
1. Task Scheduler → View → **Show All Running Tasks**
**Check 2:** Check Task Scheduler history

```
Test-Path "C:\Users\Sam\PycharmProjects\VoicemeeterSwitcher\run_api_task.bat"
```powershell
**Check 1:** Verify the path

### API doesn't start at all

3. Save and restart the task
2. General tab → Select **"Run only when user is logged on"**
1. Edit the task
**Fix:** In Task Scheduler:

**Problem:** Task is running in Session 0

### API starts but can't connect to Voicemeeter

## Troubleshooting

This ensures the task runs in your desktop session where Voicemeeter is running.
### Solution: "Run only when user is logged on"

- Voicemeeter API can't connect across sessions
- Scheduled tasks often run in **Session 0** (system services session)
- Voicemeeter runs in **Session 1** (your desktop session)
### Session Context Issue

## Why Scheduled Tasks Can Fail

   ```
   net start VoicemeeterAPI
   ```powershell
7. **Start the service:**

   - Enter your username and password
   - Select **This account**
   - Click **Log on** tab
6. **Set the service to run as your user account:**

   - **Service name:** `VoicemeeterAPI`
   - **Arguments:** `api:app --host 0.0.0.0 --port 5000`
   - **Startup directory:** `C:\Users\Sam\PycharmProjects\VoicemeeterSwitcher`
   - **Path:** `C:\Users\Sam\PycharmProjects\VoicemeeterSwitcher\.venv\Scripts\uvicorn.exe`
5. **In the NSSM GUI:**
   ```
   .\nssm.exe install VoicemeeterAPI "C:\Users\Sam\PycharmProjects\VoicemeeterSwitcher\.venv\Scripts\uvicorn.exe"
   cd "C:\path\to\nssm"
   ```powershell
4. **Run:**
3. **Open PowerShell as Admin**
2. **Extract** nssm.exe to a folder
1. **Download NSSM:** https://nssm.cc/download

#### Using NSSM (Non-Sucking Service Manager)

For a true background service that starts automatically:

### Option 3: Run as a Windows Service (Advanced)

```
curl http://localhost:5000
```powershell
Check if the API is working:

Right-click the task → **Run**

#### Step 2: Test the task

   - ✅ "Attempt to restart up to: 3 times"
   - ✅ "If the task fails, restart every: 1 minute"
   - ✅ "Allow task to be run on demand"
7. **Settings tab:**

   - ✅ Uncheck "Start the task only if the computer is on AC power"
6. **Conditions tab:**

   - Start in: `C:\Users\Sam\PycharmProjects\VoicemeeterSwitcher`
   - Program: `C:\Users\Sam\PycharmProjects\VoicemeeterSwitcher\run_api_task.bat`
   - New → **Start a program**
5. **Actions tab:**

   - New → **At log on** (specific user: your account)
4. **Triggers tab:**

   - ✅ **Run with highest privileges**
   - ✅ **Run only when user is logged on** (IMPORTANT!)
   - Name: `Voicemeeter API Server`
3. **General tab:**
2. **Create Task** (not Basic Task)
1. **Open Task Scheduler** (`taskschd.msc`)

#### Step 1: Create the task with correct settings

If you must use a scheduled task, here's how to make it work:

### Option 2: Run as a Scheduled Task (More Complex)

3. Click **OK**
2. Change **Run:** to **Minimized**
1. Right-click the shortcut → **Properties**

To avoid seeing the console window:

#### Step 2: Start minimized (optional)

Now the API will start automatically when you log in!

6. **Click Finish**
5. **Click OK** → **Name it:** "Voicemeeter API"
4. **Browse to:** `C:\Users\Sam\PycharmProjects\VoicemeeterSwitcher\run_api.bat`
3. **Right-click** in the folder → **New** → **Shortcut**
2. **Press Enter** - This opens your Startup folder
1. **Press `Win+R`** and type: `shell:startup`

#### Step 1: Create a startup shortcut

Instead of a scheduled task, run the API at user login so it's in the same session as Voicemeeter:

### Option 1: Run at Startup (Recommended)

## The Solution

This happens because scheduled tasks run in a different session context than your desktop applications.

- ❌ No console window to see errors
- ❌ API starts but doesn't work properly
- ❌ API can't connect to Voicemeeter (`VBVMR_Login returned -2`)
When running the API from a Windows scheduled task, you may encounter:

## The Problem

