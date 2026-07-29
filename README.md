# Voicemeeter Settings Switcher

A Python script that cycles through your saved Voicemeeter settings.

## Setup

1. **Install dependencies:**
   ```powershell
   pip install voicemeeter-api
   ```

2. **Save your Voicemeeter settings:**
   - Configure Voicemeeter with your desired settings
   - In Voicemeeter, go to Menu → "Save Settings As..."
   - Save the XML file to the `settings` folder (will be created automatically)
   - Repeat for each configuration you want to cycle through
   - Name them descriptively (e.g., `gaming.xml`, `music.xml`, `streaming.xml`)

3. **Verify Voicemeeter version:**
   - Open `main.py` and check line 52
   - Change `'banana'` to match your version:
     - `'basic'` for Voicemeeter
     - `'banana'` for Voicemeeter Banana
     - `'potato'` for Voicemeeter Potato

## Usage

**Simple cycle (recommended):**
```powershell
python main.py
```
This will cycle to the next setting each time you run it.

**Advanced usage:**
You can modify the script or import it in another Python file:

```python
from main import VoicemeeterSettingsSwitcher

switcher = VoicemeeterSettingsSwitcher()
switcher.connect()

# Cycle forward
switcher.cycle_next()

# Cycle backward
switcher.cycle_previous()

# Load specific setting (0-based index)
switcher.load_specific(2)

# List all settings
switcher.list_settings()

switcher.disconnect()
```

## Hotkey Setup

To bind this to a hotkey:

### Using AutoHotkey (Windows):
1. Install [AutoHotkey](https://www.autohotkey.com/)
2. Create a script with:
   ```ahk
   F13::Run, python "C:\Users\Sam\PycharmProjects\VoicemeeterSwitcher\main.py"
   ```
3. Save and run the AutoHotkey script

### Using PowerToys (Windows):
1. Install [PowerToys](https://github.com/microsoft/PowerToys)
2. Open Keyboard Manager
3. Remap a key or shortcut to run:
   ```
   python "C:\Users\Sam\PycharmProjects\VoicemeeterSwitcher\main.py"
   ```

## Troubleshooting

**"No .xml settings files found"**
- Make sure you've saved Voicemeeter settings to the `settings` folder

**"Error connecting to Voicemeeter"**
- Make sure Voicemeeter is running
- Check that you're using the correct version in the script (basic/banana/potato)

**Settings not applying**
- Ensure the XML files were exported from the same Voicemeeter version you're using
- Try applying the settings manually in Voicemeeter first to verify they work

## File Structure

```
VoicemeeterSwitcher/
├── main.py              # Profile discovery, XML parsing, CLI entry point
├── controller.py        # Owns the Voicemeeter connection (fast/slow paths)
├── api.py               # FastAPI REST API server
├── pyproject.toml       # Project configuration
├── README.md            # This file
├── run_api.bat          # Start API server (port 8080)
├── run_webui.bat        # Start web UI (port 3100)
├── start_all.bat        # Start both API and web UI
├── tests/               # Test suite; runs without Voicemeeter installed
├── settings/            # Place your .xml settings files here
│   ├── 1-DeskSettings.xml
│   ├── 2-Headset.xml
│   └── ...
└── voicemeeter-web-ui/  # Next.js web interface
    ├── app/
    ├── components/
    └── ...
```

## Ports

| Service | Port | Started by |
|---------|------|------------|
| REST API | `8080` | `run_api.bat` / `start_api_background.ps1` |
| Web UI | `3100` | `run_webui.bat` |

`setup_network_access.bat` opens both in the Windows firewall.

## API Reference

Base URL: `http://localhost:8080`

| Method | Path | Purpose |
|--------|------|---------|
| `GET` | `/api/profiles` | List profiles and the current index |
| `POST` | `/api/profile/load` | Load a profile — `{"profile_name": "3-Soundbar.xml"}` |
| `POST` | `/api/profile/cycle` | Advance to the next profile |
| `GET` | `/api/status` | Current profile plus cached Voicemeeter state |
| `GET` | `/api/health` | Liveness. Always 200 while the server is up |
| `GET` | `/api/volume/a1` | Current A1 gain in dB |
| `POST` | `/api/volume/a1` | Set absolute gain — `{"gain": -12.0}` |
| `POST` | `/api/volume/a1/adjust` | Change gain relatively — `{"delta_db": -1.5}` |
| `GET` | `/api/mute/a1` | Current A1 mute state |
| `POST` | `/api/mute/a1` | Set mute — `{"muted": true}` |
| `POST` | `/api/mute/a1/toggle` | Flip mute |

Interactive docs are served at `/docs`.

### Status codes

| Code | Meaning |
|------|---------|
| `503` | Voicemeeter isn't reachable. Expected on a cold boot before Voicemeeter starts; retryable |
| `409` | A profile switch is in flight and the request was deliberately dropped |
| `400` | Value out of range (gain outside −60…+12 dB, or an implausible `delta_db`) |

`/api/health` returns 200 even when Voicemeeter is down, so a client can tell
"the API isn't running" (connection refused) from "the API is up but
Voicemeeter isn't" (`voicemeeter.connected` is `false`).

### Fast and slow paths

Gain and mute are cheap parameter writes and are applied immediately on a
persistent connection — fast enough to drive from a rotary encoder. Profile
loads reassign hardware devices, which is what actually destabilises
Voicemeeter, so they stay serialised behind a mutex with a minimum interval
between operations. See `controller.py` for details.

The Voicemeeter connection is opened lazily and retried, so the API can start
before Voicemeeter does.

### Configuration

| Variable | Default | Effect |
|----------|---------|--------|
| `VMSW_KIND` | `potato` | Voicemeeter edition: `basic`, `banana`, `potato` |
| `VMSW_MIN_PROFILE_INTERVAL` | `2.0` | Minimum seconds between profile loads |
| `VMSW_RECONNECT_PER_OPERATION` | unset | Open a fresh connection per operation (fallback) |

## Tests

```powershell
uv sync --group dev
uv run pytest
```

The Voicemeeter backend is injected, so the suite runs without Voicemeeter
installed — and on non-Windows machines.

## Remote Control Options

### 1. Web Interface
Modern, responsive web UI - works on desktop, tablet, and mobile.
Includes A1 volume control.

### 2. REST API
Programmatic control via HTTP - see the API Reference above.

### 3. iPhone Shortcuts
Control with Siri voice commands by POSTing to the endpoints above.

### 4. Command Line
Direct Python script execution
- `python main.py` to cycle profiles

## Features

✅ **Profile Switching** - Cycle through saved Voicemeeter configurations
✅ **Web UI** - Beautiful, responsive interface for all devices
✅ **REST API** - HTTP endpoints for automation and integration
✅ **Volume Control** - Adjust A1 output volume from web UI or API
✅ **Status Monitoring** - Real-time display of current profile and settings
✅ **Mobile Support** - Full touch support for phones and tablets
✅ **Background Mode** - Run API server as Windows service
✅ **Network Access** - Control from any device on your network
✅ **Crash Protection** - Thread-safe operations with rate limiting

