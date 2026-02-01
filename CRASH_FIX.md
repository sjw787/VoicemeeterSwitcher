# Fixed: Voicemeeter Crashing Issue

## The Problem

Voicemeeter was crashing when interacting with the web UI because:
- ❌ Each API request created a NEW Voicemeeter connection
- ❌ Rapid profile switches caused multiple concurrent connections
- ❌ Connection creation/destruction cycles stressed Voicemeeter
- ❌ Not enough time between profile switches

## The Solution

I've made several critical fixes:

### 1. **Single Persistent Connection**

**Before:**
```python
# Created a NEW connection for EVERY request
with voicemeeterlib.api('potato') as vmr:
    switcher.load_setting(vmr, profile_path)
```

**After:**
```python
# Use ONE persistent connection for ALL requests
vmr = get_vmr()  # Reuses existing connection
switcher.load_setting(vmr, profile_path)
```

### 2. **Automatic Reconnection**

If the connection is lost, the API now:
- Detects the failure
- Clears the old connection
- Automatically reconnects
- Retries the operation

### 3. **Increased Stabilization Time**

- Changed from `0.5` seconds to `1.5` seconds after profile load
- Gives Voicemeeter time to apply all settings before next operation

### 4. **Connection Lifecycle**

- ✅ Connection created **once** on API startup
- ✅ Reused for **all** subsequent requests
- ✅ Only recreated if it fails
- ✅ No more repeated connect/disconnect cycles

## What Changed

### `api.py` Changes:

1. **Added persistent connection:**
   ```python
   vmr_connection = None
   
   def get_vmr():
       global vmr_connection
       if vmr_connection is None:
           vmr_connection = voicemeeterlib.api('potato')
           vmr_connection.login()
       return vmr_connection
   ```

2. **Updated profile loading:**
   - Now uses `get_vmr()` instead of `with voicemeeterlib.api(...)`
   - Includes retry logic with reconnection

3. **Updated cycle function:**
   - Uses persistent connection
   - Includes automatic reconnection

### `main.py` Changes:

1. **Increased delay:**
   - `time.sleep(0.5)` → `time.sleep(1.5)`
   - Prevents rapid-fire profile switches

## How to Apply

**You MUST restart the API server:**

1. **Stop the current API:**
   - Find the terminal running the API
   - Press `Ctrl+C`

2. **Start it again:**
   ```
   run_api.bat
   ```

3. **You should see:**
   ```
   ✓ Connected to Voicemeeter
   ```

## Benefits

✅ **No more crashes** - Single connection prevents stress on Voicemeeter  
✅ **Faster responses** - No connection overhead per request  
✅ **Auto-recovery** - Reconnects automatically if connection lost  
✅ **More stable** - Longer delays between operations  
✅ **Better logging** - Clear connection status messages  

## Testing

After restarting the API:

1. **Try switching profiles** from the web UI
2. **Switch rapidly** - should handle it gracefully now
3. **Check the API console** - you should see:
   ```
   ✓ Connected to Voicemeeter
   Received request to load profile: ...
   load_setting returned: True
   ```

## Troubleshooting

### API won't start - "Failed to connect to Voicemeeter"

**Solution:** Make sure Voicemeeter is running BEFORE starting the API

1. Start Voicemeeter Potato
2. Wait 5 seconds for it to initialize
3. Start the API: `run_api.bat`

### Still getting crashes?

**Try these:**

1. **Close ALL Voicemeeter instances:**
   - Open Task Manager (Ctrl+Shift+Esc)
   - End all `voicemeeter*.exe` processes
   - Restart Voicemeeter

2. **Restart the API:**
   - Stop with Ctrl+C
   - Run `run_api.bat` again

3. **Increase the delay even more:**
   - Edit `main.py`
   - Change `time.sleep(1.5)` to `time.sleep(2.0)` or `time.sleep(3.0)`
   - Restart API

### "Connection lost" messages?

The API will automatically reconnect. You should see:
```
✗ Failed during operation: ...
✓ Reconnected to Voicemeeter
✓ Retry successful
```

## Technical Details

### Why This Fixes Crashes

**Root Cause:**
- Voicemeeter's API has limits on connection frequency
- Creating/destroying connections rapidly causes instability
- Multiple concurrent connections can conflict

**Solution:**
- Single persistent connection = no creation/destruction overhead
- Reused connection = no API stress
- Longer delays = Voicemeeter has time to process changes

### Connection Lifecycle

```
API Startup
└─ Connect to Voicemeeter → vmr_connection
   
Profile Switch #1
└─ Use vmr_connection (no new connection)

Profile Switch #2  
└─ Use vmr_connection (no new connection)

Connection Error
├─ Clear vmr_connection
├─ Reconnect
└─ Retry operation
```

## Summary

✅ **Single persistent Voicemeeter connection** - No more repeated connect/disconnect  
✅ **Automatic reconnection** - Handles connection loss gracefully  
✅ **Longer stabilization time** - Voicemeeter has time to process changes  
✅ **Better error handling** - Clear messages and automatic recovery  

**Restart the API and Voicemeeter should stop crashing!** 🎉
