# Fix Applied: Better Error Handling for Profile Loading

## Problem
When clicking profile cards, you were getting:
```
POST http://localhost:5000/api/profile/load 400 (Bad Request)
```

But the error message didn't show WHY it failed.

## Changes Made

### 1. Enhanced Web UI Error Handling (`app/page.tsx`)
**Before:** Generic "Failed to load profile" message

**After:**
- Parses the actual error from the API
- Logs the full error details to console
- Shows the specific error message to the user
- Added console logging to track what's being sent

### 2. Enhanced API Error Handling (`api.py`)
**Before:** Silent failures or generic errors

**After:**
- Logs every step of profile loading
- Shows which file is being requested
- Lists available files if profile not found
- Catches and logs Voicemeeter connection errors
- Returns specific error messages (not just 400)
- Includes full stack traces in console

## How to Debug Now

### Step 1: Restart the API Server
The API needs to be restarted to use the new code:
1. Close the API window (if running)
2. Run `run_api.bat` again

### Step 2: Try Loading a Profile
1. Open the web UI: http://localhost:3000
2. Click a profile card
3. Watch BOTH:
   - Browser console (F12 → Console tab)
   - API server window

### Step 3: Check the Logs

**In the Browser Console, you'll see:**
```
Loading profile: 2-Headset.xml
```

**In the API Window, you'll see:**
```
Received request to load profile: 2-Headset.xml
  Checking file 0: 1-DeskSettings.xml
  Checking file 1: 2-Headset.xml
Found profile at index 1: C:\Users\Sam\...\settings\2-Headset.xml
load_setting returned: True
Successfully loaded profile: Headset
```

**If there's an error, you'll see exactly what went wrong:**
- Profile file not found → Lists all available files
- Voicemeeter not running → "Voicemeeter error: ..."
- XML parsing error → Full error details
- Device not found → Specific device error

## Common Issues and Solutions

### Issue 1: "Profile not found"
**Cause:** Filename mismatch

**Solution:** Check the console for "Available files:" list. Make sure the filename matches exactly.

### Issue 2: "Voicemeeter error: ..."
**Cause:** Voicemeeter not running or wrong version

**Solution:** 
1. Start Voicemeeter Potato
2. Check `api.py` line 77 - should be `'potato'`
3. Change to `'banana'` or `'basic'` if needed

### Issue 3: "Failed to load profile - check Voicemeeter is running"
**Cause:** load_setting returned False

**Solution:** 
1. Make sure Voicemeeter is running
2. Check the XML files are valid
3. Look at the API console for warnings about specific devices

### Issue 4: Connection refused
**Cause:** API server not running

**Solution:** Run `run_api.bat`

## Testing

Run `test_api.bat` to verify:
- API is running
- Profiles are available
- Status endpoint works

## Next Steps

1. **Restart API:** Close and run `run_api.bat`
2. **Refresh Web UI:** Hard refresh (Ctrl+Shift+R)
3. **Try again:** Click a profile card
4. **Check logs:** Look at both browser and API console
5. **Report back:** Tell me the exact error message you see

The error messages will now be much more helpful!
