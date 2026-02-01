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
├── main.py              # Main script
├── api.py               # FastAPI REST API server
├── pyproject.toml       # Project configuration
├── README.md            # This file
├── API_USAGE.md         # API documentation
├── WEB_UI_GUIDE.md      # Web UI documentation
├── run_api.bat          # Start API server
├── run_webui.bat        # Start web UI
├── start_all.bat        # Start both API and web UI
├── settings/            # Place your .xml settings files here
│   ├── 1-DeskSettings.xml
│   ├── 2-Headset.xml
│   └── ...
└── voicemeeter-web-ui/  # Next.js web interface
    ├── app/
    ├── components/
    └── ...
```

## Remote Control Options

### 1. Web Interface
Modern, responsive web UI - works on desktop, tablet, and mobile
- See [WEB_UI_GUIDE.md](WEB_UI_GUIDE.md)

### 2. REST API
Programmatic control via HTTP API
- See [API_USAGE.md](API_USAGE.md)

### 3. iPhone Shortcuts
Control with Siri voice commands
- See [API_USAGE.md](API_USAGE.md) → iPhone Shortcuts section

### 4. Command Line
Direct Python script execution
- `python main.py` to cycle profiles

