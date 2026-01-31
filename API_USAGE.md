# Voicemeeter API Usage Guide

## Starting the API Server

Run the API server using the provided batch file:
```bash
run_api.bat
```

Or manually:
```bash
.\.venv\Scripts\activate
uvicorn api:app --host 0.0.0.0 --port 5000 --reload
```

## Finding Your PC's IP Address or Computer Name

### Option 1: Use Computer Name (Recommended)

Find your computer name:
```powershell
$env:COMPUTERNAME
```

Then use it with `.local` extension (works on iPhone automatically via mDNS):
```
http://YOUR-COMPUTER-NAME.local:5000
```

For example, if your computer name is "Sam-PC":
```
http://Sam-PC.local:5000/api/profiles
```

### Option 2: Use IP Address

Run this command in PowerShell:
```powershell
Get-NetIPAddress -AddressFamily IPv4 | Where-Object {$_.IPAddress -like "192.168.*" -or $_.IPAddress -like "10.*"}
```

Or simply:
```cmd
ipconfig
```
Look for "IPv4 Address" (e.g., `192.168.1.100`)

**Note:** Using the computer name (`.local`) is more convenient because it doesn't change if your router assigns a different IP address.

## API Endpoints

### 1. Get All Profiles
**Endpoint:** `GET /api/profiles`

**Example URL:** `http://192.168.1.100:5000/api/profiles`

**Response:**
```json
{
  "profiles": [
    {
      "filename": "1-DeskSettings.xml",
      "display_name": "DeskSettings",
      "index": 0
    },
    {
      "filename": "2-Headset.xml",
      "display_name": "Headset",
      "index": 1
    }
  ],
  "current_index": 0,
  "total": 2
}
```

### 2. Load Specific Profile
**Endpoint:** `POST /api/profile/load`

**Example URL:** `http://192.168.1.100:5000/api/profile/load`

**Request Body:**
```json
{
  "profile_name": "2-Headset.xml"
}
```

**Response:**
```json
{
  "status": "success",
  "message": "Loaded Headset",
  "profile": "2-Headset.xml"
}
```

### 3. Cycle to Next Profile
**Endpoint:** `POST /api/profile/cycle`

**Example URL:** `http://192.168.1.100:5000/api/profile/cycle`

**Response:**
```json
{
  "status": "success",
  "message": "Switched to Headset",
  "current_profile": "2-Headset.xml",
  "current_index": 1
}
```

### 4. Get Current Status
**Endpoint:** `GET /api/status`

**Example URL:** `http://192.168.1.100:5000/api/status`

**Response:**
```json
{
  "status": "running",
  "current_profile": "2-Headset.xml",
  "current_display_name": "Headset",
  "current_index": 1,
  "total_profiles": 4,
  "settings_dir": "C:\\Users\\Sam\\PycharmProjects\\VoicemeeterSwitcher\\settings"
}
```

## iPhone Shortcuts Setup

### Creating a Shortcut to Load a Profile

1. Open the **Shortcuts** app on your iPhone
2. Tap **+** to create a new shortcut
3. Add **"Get Contents of URL"** action
4. Configure:
   - **URL:** `http://YOUR-COMPUTER-NAME.local:5000/api/profile/load` (replace YOUR-COMPUTER-NAME with your actual computer name)
   - **Method:** `POST`
   - **Request Body:** `JSON`
   - **JSON:** 
     ```json
     {"profile_name": "2-Headset.xml"}
     ```
5. (Optional) Add **"Show Result"** action to see the response
6. Name your shortcut (e.g., "Load Headset")
7. Add to home screen or use with Siri

**Example:** If your computer name is "Sam-PC", use: `http://Sam-PC.local:5000/api/profile/load`

### Creating a Shortcut to Cycle Profiles

1. Create a new shortcut
2. Add **"Get Contents of URL"** action
3. Configure:
   - **URL:** `http://YOUR-COMPUTER-NAME.local:5000/api/profile/cycle`
   - **Method:** `POST`
4. (Optional) Add **"Show Result"** action
5. Name it "Next Audio Profile"

### Creating Shortcuts for Each Profile

Create separate shortcuts for each of your profiles:

**Headset:**
```json
{"profile_name": "2-Headset.xml"}
```

**Soundbar:**
```json
{"profile_name": "3-Soundbar.xml"}
```

**TV Speakers:**
```json
{"profile_name": "4-TvSpeakers.xml"}
```

**Desk Settings:**
```json
{"profile_name": "1-DeskSettings.xml"}
```

## Siri Voice Commands

Once you've created shortcuts, you can trigger them with Siri:
- "Hey Siri, Load Headset"
- "Hey Siri, Next Audio Profile"
- "Hey Siri, Load Soundbar"

## Interactive API Documentation

While the server is running, visit these URLs in your browser:
- **Swagger UI:** `http://localhost:5000/docs`
- **ReDoc:** `http://localhost:5000/redoc`

## Troubleshooting

### Can't Connect from iPhone
1. Make sure both devices are on the same WiFi network
2. Check Windows Firewall - allow port 5000:
   ```powershell
   New-NetFirewallRule -DisplayName "Voicemeeter API" -Direction Inbound -LocalPort 5000 -Protocol TCP -Action Allow
   ```
3. Verify the API is running (check `http://localhost:5000` on your PC)
4. Double-check your PC's IP address

### Profile Not Found Error
Make sure the `profile_name` matches exactly the filename in your `settings` folder, including the `.xml` extension.

### Server Won't Start
Make sure Voicemeeter is installed and running, and that the virtual environment is activated.
