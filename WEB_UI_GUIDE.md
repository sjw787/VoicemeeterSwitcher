# Voicemeeter Web UI - Quick Start Guide

## What You Get

A beautiful, modern web interface to control your Voicemeeter audio profiles from any device on your network!

## Features

- 🎵 View all your audio profiles in a card layout
- ✅ Real-time display of the active profile
- 🔄 One-click switching between profiles
- ⏭️ Quick "Cycle to Next" button
- 📱 Mobile-responsive (use from your phone!)
- 🎨 Beautiful dark theme with smooth animations
- 🔄 Auto-refresh every 2 seconds

## Setup (One Time Only)

### Step 1: Start the API Server
The web UI needs the API server running. Use the batch file:
```bash
run_api.bat
```

Or start it manually:
```bash
cd C:\Users\Sam\PycharmProjects\VoicemeeterSwitcher
.\.venv\Scripts\activate
uvicorn api:app --host 0.0.0.0 --port 5000 --reload
```

### Step 2: Start the Web UI

**Option A: Development Mode (Recommended for testing)**
```bash
run_webui.bat
```

Or manually:
```bash
cd voicemeeter-web-ui
npm run dev
```

**Option B: Production Mode (Faster, more stable)**
```bash
cd voicemeeter-web-ui
npm run build
npm start
```

### Step 3: Open in Browser
- **On your PC:** http://localhost:3000
- **From your phone:** http://YOUR-COMPUTER-NAME.local:3000
  - Find your computer name: `$env:COMPUTERNAME` in PowerShell

## Using the Web UI

### Desktop/Laptop
1. Open http://localhost:3000 in any browser
2. Click any profile card to switch to that profile
3. Or click "Cycle to Next Profile" to go to the next one
4. The active profile is highlighted in green with a pulsing dot

### Mobile Phone (iPhone/Android)
1. Make sure your phone is on the same WiFi network
2. Open Safari/Chrome
3. Go to: http://YOUR-COMPUTER-NAME.local:3000
4. Use it like a native app!
5. (Optional) Add to home screen for quick access

### iPad/Tablet
Same as mobile - works great on larger screens!

## Firewall Setup (If Mobile Can't Connect)

If you can't access from your phone, add firewall rules:

```powershell
# Allow Web UI port (3000)
New-NetFirewallRule -DisplayName "Voicemeeter Web UI" -Direction Inbound -LocalPort 3000 -Protocol TCP -Action Allow

# Allow API port (5000) - if not already done
New-NetFirewallRule -DisplayName "Voicemeeter API" -Direction Inbound -LocalPort 5000 -Protocol TCP -Action Allow
```

## Configuration

Edit `.env.local` in the `voicemeeter-web-ui` folder to change settings:

```env
# Default - for local access only
NEXT_PUBLIC_API_URL=http://localhost:5000

# For network access - use your computer name
NEXT_PUBLIC_API_URL=http://YOUR-COMPUTER-NAME.local:5000

# Or use IP address (but this may change)
NEXT_PUBLIC_API_URL=http://192.168.1.100:5000
```

## Tips & Tricks

### Add to iPhone Home Screen
1. Open the web UI in Safari
2. Tap the Share button
3. Tap "Add to Home Screen"
4. Now it launches like a native app!

### Auto-Start Everything
Create a batch file to start both API and Web UI:

```batch
@echo off
start "" "C:\Users\Sam\PycharmProjects\VoicemeeterSwitcher\run_api.bat"
timeout /t 3
start "" "C:\Users\Sam\PycharmProjects\VoicemeeterSwitcher\run_webui.bat"
```

### Use with Voice Assistants
- **iPhone Shortcuts:** Create shortcuts that call the API (see API_USAGE.md)
- **Web UI:** Open directly from Siri by adding to home screen and naming it

## Troubleshooting

### "Failed to connect to Voicemeeter API"
- Make sure `run_api.bat` is running
- Check that Voicemeeter is installed and running
- Verify the API URL in browser: http://localhost:5000

### Mobile Can't Access
- Confirm both devices are on the same WiFi
- Add firewall rules (see above)
- Try using IP address instead of computer name
- Restart the web UI server

### Page Doesn't Load / White Screen
- Clear browser cache
- Try incognito/private browsing mode
- Check browser console for errors (F12)
- Rebuild: `npm run build && npm start`

### Profiles Not Showing
- Make sure your XML files are in the `settings` folder
- Check the API status: http://localhost:5000/api/status
- Look at the API console for error messages

## Technical Details

### Tech Stack
- **Frontend:** Next.js 15, React, TypeScript
- **Styling:** Tailwind CSS
- **Backend:** FastAPI (Python)
- **Communication:** REST API with auto-refresh

### Ports Used
- **3000:** Web UI (Next.js dev server)
- **5000:** API Server (FastAPI)

### Development
Edit files in:
- `voicemeeter-web-ui/app/page.tsx` - Main page
- `voicemeeter-web-ui/components/` - Reusable components
- `voicemeeter-web-ui/app/globals.css` - Global styles

Hot reload is enabled in dev mode - changes appear instantly!

## What's Next?

The web UI currently supports:
- Viewing profiles
- Switching profiles
- Cycling profiles
- Real-time status

Future enhancements could include:
- Volume controls for each strip/bus
- Mute/unmute buttons
- Input device selection
- Output device selection
- Custom profile colors/icons
- Keyboard shortcuts
- Dark/light theme toggle

Enjoy your new Voicemeeter web interface! 🎉
