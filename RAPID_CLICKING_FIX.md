# Fixed: Rapid Profile Switching Issue

## Problem
When clicking between profile cards too fast, you got this error:
```
CAPIError: VBVMR_Login returned -2
```

This happens because Voicemeeter's API can't handle multiple login attempts simultaneously. Each profile switch opens a new connection, and if the previous one is still active, it fails.

## Solution Implemented

I've added **smart debouncing and visual feedback** to handle this gracefully:

### 1. **Prevents Concurrent Switches**
- Only one profile can be loading at a time
- Additional clicks are ignored while loading
- Console logs "Profile switch already in progress"

### 2. **Visual Loading State**
When you click a profile card:
- **Blue glow** - Profile is loading
- **Spinner icon** - Shows activity in top-right corner
- **Button shows "⏳ Loading..."**
- **Card is unclickable** while loading

### 3. **Error Handling with Yellow Warning**
If a switch fails (e.g., too fast, device off):
- **Yellow/amber glow** - Warning state
- **⚠️ icon** - Shows there was an issue
- **Button shows "⚠️ Try Again"** - Click to retry
- **User-friendly message** - "Please wait - previous profile is still loading"
- **Auto-clears after 3 seconds**

### 4. **Active State (Unchanged)**
When a profile is active:
- **Green glow** - Active state
- **Pulsing dot** - Shows it's the current profile
- **Button shows "✓ Active"**

## Visual States Summary

| State | Border/Glow | Icon | Button | Clickable |
|-------|-------------|------|--------|-----------|
| **Inactive** | Gray | - | "Load Profile" | ✅ Yes |
| **Loading** | Blue | 🔄 Spinner | "⏳ Loading..." | ❌ No |
| **Error** | Yellow | ⚠️ Warning | "⚠️ Try Again" | ✅ Yes |
| **Active** | Green | 🟢 Pulse | "✓ Active" | ❌ No |

## How It Works Now

### Scenario 1: Normal Click
1. Click profile → Blue glow + spinner
2. ~1 second later → Green glow (active)
3. Other cards return to gray

### Scenario 2: Rapid Clicking
1. Click Profile A → Blue glow + spinner
2. Try to click Profile B → **Ignored** (A still loading)
3. Profile A finishes → Green glow
4. Now you can click Profile B

### Scenario 3: Error (Too Fast)
1. Click Profile A → Blue glow
2. API error (still busy) → Yellow glow + warning
3. Wait a moment
4. Click "⚠️ Try Again" → Blue glow → Green glow

## User Experience Improvements

✅ **Visual feedback** - Always know what's happening  
✅ **No more confusing errors** - Yellow warning instead of error message  
✅ **Can retry easily** - Just click the yellow card again  
✅ **Prevents spam clicking** - Ignores clicks during loading  
✅ **Auto-recovery** - Error state clears after 3 seconds  
✅ **Better error messages** - "Please wait" instead of "VBVMR_Login -2"

## To Use

1. **Refresh the web page** (Ctrl+Shift+R)
2. **Click profiles normally** - Loading indicator appears
3. **If it turns yellow** - Wait a second, then try again
4. **When it's green** - Profile is active!

## Technical Details

**Frontend Changes:**
- Added `switchingProfile` state to track loading
- Added `profileError` state to track errors
- Prevents concurrent API calls
- Passes loading/error states to ProfileCard
- Auto-clears errors after 3 seconds

**ProfileCard Changes:**
- New props: `isLoading`, `hasError`
- Dynamic styling based on state
- Loading spinner animation
- Warning icon for errors
- Different button text per state

**No Backend Changes Needed** - All handled in frontend!

## Next Steps

The web UI now gracefully handles rapid clicking. Just refresh the page and try it!

If you still see issues:
1. Wait 1-2 seconds between clicks
2. If a card turns yellow, try clicking it again
3. Check the API logs for other errors
