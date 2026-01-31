# Instructions: Getting Your Settings Files

## Step 1: Save Your Current Voicemeeter Configuration

1. **Open Voicemeeter** (Basic, Banana, or Potato)
2. **Configure it** with your desired settings (routing, levels, effects, etc.)
3. Click on **Menu** (top-left corner)
4. Select **"Save Settings As..."** or **"Load/Save Settings" → "Save As..."**
5. Navigate to this `settings` folder:
   `C:\Users\Sam\PycharmProjects\VoicemeeterSwitcher\settings`
6. Give it a descriptive name, e.g., `gaming.xml`, `music.xml`, `streaming.xml`
7. Click **Save**

## Step 2: Create Multiple Configurations

Repeat Step 1 for each configuration you want to switch between:
- Gaming setup
- Music production
- Streaming/recording
- Video calls
- etc.

## Step 3: Delete the Example File

Once you have your real settings files, you can delete `example.xml`

## Step 4: Run the Script

```powershell
python main.py
```

The script will:
- List all your saved settings
- Cycle to the next one
- Apply it to Voicemeeter

Each time you run it, it advances to the next setting in alphabetical order.

## Tips

- **Name files alphabetically** if you want them in a specific order (e.g., `1-gaming.xml`, `2-music.xml`, `3-streaming.xml`)
- **Bind to a hotkey** for instant switching (see README.md for instructions)
- The script remembers which setting was loaded last and cycles to the next one
