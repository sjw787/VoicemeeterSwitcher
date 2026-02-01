# Network Access Setup Guide

## Problem
You can access the web UI on your PC (localhost:3000) but not from other devices on your network.

## Solution - 3 Steps

### Step 1: Configure Next.js to Accept Network Connections

✅ **Already Done!** I've updated `package.json` to use `-H 0.0.0.0` which allows network access.

### Step 2: Add Firewall Rules

✅ **Already Done!** I've added a Windows Firewall rule for port 3000.

To verify, run:
```powershell
Get-NetFirewallRule -DisplayName "Voicemeeter Web UI (Port 3000)"
```

If you need to add it manually:
```powershell
New-NetFirewallRule -DisplayName "Voicemeeter Web UI (Port 3000)" -Direction Inbound -LocalPort 3000 -Protocol TCP -Action Allow
```

**Also ensure the API port (5000) is open:**
```powershell
New-NetFirewallRule -DisplayName "Voicemeeter API (Port 5000)" -Direction Inbound -LocalPort 5000 -Protocol TCP -Action Allow
```

### Step 3: Find Your Computer's Network Address

**Option A: Use Computer Name (Recommended)**

Run this in PowerShell:
```powershell
hostname
```

Your devices can access the web UI at:
```
http://YOUR-COMPUTER-NAME.local:3000
```

**Option B: Use IP Address**

Run this in PowerShell:
```powershell
ipconfig
```

Look for "IPv4 Address" under your active network adapter (usually starts with 192.168.x.x).

Your devices can access the web UI at:
```
http://YOUR-IP-ADDRESS:3000
```

For example: `http://192.168.1.100:3000`

### Step 4: Update the API URL

**Important!** If accessing from other devices, you need to update `.env.local`:

1. Open `voicemeeter-web-ui\.env.local`
2. Change this line:
   ```env
   NEXT_PUBLIC_API_URL=http://localhost:5000
   ```
   
3. To use your computer name:
   ```env
   NEXT_PUBLIC_API_URL=http://YOUR-COMPUTER-NAME:5000
   ```
   
   Or use your IP address:
   ```env
   NEXT_PUBLIC_API_URL=http://192.168.1.100:5000
   ```

4. **Restart the web UI** (stop and run `run_webui.bat` again)

### Step 5: Restart the Web UI

**Stop the current server:**
- Press `Ctrl+C` in the web UI terminal

**Start it again:**
```
run_webui.bat
```

## Testing Network Access

### From Your Phone/Tablet

1. **Make sure you're on the same WiFi network** as your PC
2. **Open your browser** (Safari, Chrome, etc.)
3. **Try these URLs:**

   **Option A - Computer Name:**
   ```
   http://YOUR-COMPUTER-NAME.local:3000
   ```
   
   **Option B - IP Address:**
   ```
   http://192.168.1.100:3000
   ```
   (Replace with your actual IP)

### Quick Test

Run this from PowerShell to see your access URLs:
```powershell
$hostname = hostname
$ip = (Get-NetIPAddress -AddressFamily IPv4 | Where-Object { $_.IPAddress -notlike '169.*' -and $_.IPAddress -ne '127.0.0.1' -and $_.PrefixOrigin -ne 'WellKnown' } | Select-Object -First 1).IPAddress

Write-Host "`nAccess the web UI from other devices using:`n"
Write-Host "  Option 1 (Computer Name): http://${hostname}.local:3000"
Write-Host "  Option 2 (IP Address):    http://${ip}:3000`n"
Write-Host "Make sure to update .env.local with:`n"
Write-Host "  NEXT_PUBLIC_API_URL=http://${hostname}:5000"
Write-Host "  or"
Write-Host "  NEXT_PUBLIC_API_URL=http://${ip}:5000`n"
```

## Troubleshooting

### Can't Connect from Phone

**Check 1: Same Network?**
- PC and phone must be on the same WiFi

**Check 2: Firewall Rules?**
```powershell
# Check if rules exist
Get-NetFirewallRule -DisplayName "*Voicemeeter*"

# Add if missing
New-NetFirewallRule -DisplayName "Voicemeeter Web UI (Port 3000)" -Direction Inbound -LocalPort 3000 -Protocol TCP -Action Allow
New-NetFirewallRule -DisplayName "Voicemeeter API (Port 5000)" -Direction Inbound -LocalPort 5000 -Protocol TCP -Action Allow
```

**Check 3: Server Binding?**
Make sure `package.json` has `-H 0.0.0.0`:
```json
"dev": "next dev -H 0.0.0.0"
```

**Check 4: .env.local Updated?**
Must use computer name or IP, not localhost:
```env
NEXT_PUBLIC_API_URL=http://YOUR-COMPUTER-NAME:5000
```

**Check 5: Web UI Restarted?**
After changing `.env.local`, you MUST restart the web UI server!

### Network Discovery Issues

**Windows Network Discovery:**
If `.local` addresses don't work, enable network discovery:
1. Open Settings → Network & Internet
2. Click your network type (WiFi or Ethernet)
3. Click "Advanced sharing settings"
4. Turn on "Network discovery"

**Or just use the IP address instead!**

### API Also Needs Network Access

The API server (`run_api.bat`) is already configured to use `0.0.0.0` in the command:
```bash
uvicorn api:app --host 0.0.0.0 --port 5000 --reload
```

If not, update `run_api.bat` to include `--host 0.0.0.0`.

## Summary Checklist

- [x] Updated `package.json` to use `-H 0.0.0.0`
- [x] Added firewall rules for ports 3000 and 5000
- [ ] Find your computer name: `hostname`
- [ ] Find your IP address: `ipconfig`
- [ ] Update `.env.local` with your computer name or IP
- [ ] Restart web UI: `run_webui.bat`
- [ ] Test from phone: `http://YOUR-PC-NAME.local:3000`

## Quick Setup Script

Save this as `setup_network_access.bat`:

```batch
@echo off
echo Setting up network access...
echo.

echo [1/3] Getting network info...
hostname
ipconfig | findstr IPv4

echo.
echo [2/3] Adding firewall rules...
netsh advfirewall firewall add rule name="Voicemeeter Web UI" dir=in action=allow protocol=TCP localport=3000
netsh advfirewall firewall add rule name="Voicemeeter API" dir=in action=allow protocol=TCP localport=5000

echo.
echo [3/3] Done!
echo.
echo Update .env.local with your computer name or IP from above
echo Then restart the web UI server
echo.
pause
```

After setup, access from other devices at:
- `http://YOUR-COMPUTER-NAME.local:3000`
- or `http://YOUR-IP-ADDRESS:3000`
