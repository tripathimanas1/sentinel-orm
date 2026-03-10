# How to Fix the "Card Not Clickable" Issue

## The Problem
Your browser has cached the old version of the JavaScript file, so it's not loading the new click handlers.

## The Solution - HARD REFRESH

### Option 1: Hard Refresh (Recommended)
1. Go to http://localhost:3000
2. Press one of these key combinations:
   - **Windows/Linux**: `Ctrl + Shift + R` or `Ctrl + F5`
   - **Mac**: `Cmd + Shift + R`

This will force the browser to reload all files, bypassing the cache.

### Option 2: Clear Browser Cache
1. Open Developer Tools (F12)
2. Right-click on the refresh button
3. Select "Empty Cache and Hard Reload"

### Option 3: Incognito/Private Window
1. Open a new Incognito/Private window
2. Navigate to http://localhost:3000
3. This will load the page without any cached files

## Verification Steps

After doing a hard refresh:

1. **Open Developer Console** (F12)
2. **Click on a source card** (Twitter, Reddit, Instagram, or Quora)
3. **Check the console** - You should see:
   ```
   Card clicked for platform: twitter
   showLLMDetails called for: twitter {data object}
   ```
4. **Modal should appear** with detailed LLM visibility information

## What Changed

I've added cache-busting version parameters to both files:
- `app.js?v=2` - Contains the click handlers and modal code
- `style.css?v=2` - Contains the modal styling

These version parameters force the browser to treat them as new files.

## If It Still Doesn't Work

1. Check the browser console (F12 → Console tab) for any errors
2. Verify the files are loading:
   - Go to Network tab in DevTools
   - Refresh the page
   - Look for `app.js?v=2` and `style.css?v=2`
   - They should show status 200

3. If you see the console logs but no modal appears, there might be a JavaScript error - share the console output with me.
