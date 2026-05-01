# Reddit Comment Assistant - Chrome Extension

AI-powered Chrome extension for generating Reddit comments.

## Setup

1. **Backend First**: Ensure the FastAPI backend is running:
   ```bash
   cd /path/to/reddit
   source venv/bin/activate
   uvicorn app.main:app --port 8000
   ```

2. **Chrome Extension Icons** (IMPORTANT):
   - Chrome ExtensionManifest V3 requires PNG icons
   - Convert the SVG files in `icons/` folder to PNG:
     - `icon16.svg` → `icon16.png` (16x16)
     - `icon48.svg` → `icon48.png` (48x48)
     - `icon128.svg` → `icon128.png` (128x128)
   - Use any online SVG to PNG converter or design tool

3. **Load Extension in Chrome**:
   - Open Chrome and go to `chrome://extensions/`
   - Enable "Developer mode" (top right)
   - Click "Load unpacked"
   - Select the `chrome-extension` folder

4. **Configure API URL** (if backend is not on localhost:8000):
   - Edit `popup.js` and change `API_BASE` constant

## Usage

1. **Login**: Open the extension popup and register/login
2. **Create Personas**: Add comment personas (e.g., "Professional Marketer", "Casual Friend")
3. **Browse Reddit**: Go to any Reddit post
4. **Extract Post**: Click the floating "Extract Post" button
5. **Generate Comments**: Select a persona (optional) and click "Generate Comments"
6. **Copy & Use**: Click "Copy" on any generated comment to copy and mark as used

## Features

- Email/password authentication
- Google OAuth support (configure GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET)
- Multiple persona support
- Reddit post content extraction
- AI-powered comment generation (DeepSeek)
- Comment usage tracking
- Rate limiting (10 requests/minute)

## API Configuration

Set these environment variables for the backend:

```bash
DEEPSEEK_API_KEY=your_api_key  # Optional, uses mock data if not set
JWT_SECRET_KEY=your_secret_key
MYSQL_HOST=mysql
REDIS_HOST=redis
```

## Files

- `manifest.json` - Extension configuration
- `popup.html/css/js` - Extension popup UI
- `content.js` - Reddit page content extraction
- `background.js` - Service worker
