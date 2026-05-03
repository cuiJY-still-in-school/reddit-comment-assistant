# Reddit Comment Assistant

AI-powered Reddit comment generation system with Chrome extension.

---

## 🚀 Quick Start

```bash
# 1. Start infrastructure
docker compose up -d mysql redis

# 2. Install dependencies
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# 3. Configure API Key
# Edit .env and add your DeepSeek API key:
# DEEPSEEK_API_KEY=your-key-here

# 4. Run
uvicorn app.main:app --port 8000
```

---

## 📥 Pre-built Executables

| Platform | Architecture | File | Status |
|----------|-------------|------|--------|
| Linux | x86_64 | `build-tools/dist/reddit-assistant-linux-x86_64.sh` | ✅ Ready |
| Linux | ARM64 | `build-tools/dist/reddit-assistant-linux-arm64.sh` | ✅ Ready |
| macOS | M1/M2/M3/M4 | `build-tools/dist/reddit-assistant-mac-arm64.sh` | ✅ Ready |
| macOS | Intel | `build-tools/install-mac.sh` | ✅ Ready |
| Windows | x86_64 | Build with PyInstaller (see below) | Build |

---

## 📁 Project Structure

```
reddit/
├── app/                    # FastAPI Backend
│   ├── api/               # API routes (auth, persona, comment)
│   ├── models/            # SQLAlchemy models (4 tables)
│   ├── schemas/           # Pydantic schemas
│   ├── services/          # Business logic
│   ├── utils/             # Security, cache, rate limiter
│   └── main.py            # FastAPI entry
├── chrome-extension/       # Chrome Extension
├── build-tools/            # Build & Setup tools
│   ├── launcher.py        # PyInstaller launcher
│   ├── install.sh         # Linux installer
│   ├── install-mac.sh     # Mac installer
│   ├── install.bat        # Windows installer
│   └── dist/              # Built executables
└── docker-compose.yml     # MySQL + Redis
```

---

## 🔧 Chrome Extension Setup

1. Open `chrome://extensions/`
2. Enable **Developer mode**
3. Click **Load unpacked**
4. Select `chrome-extension/` folder

**Features:**
- Right-click any selected text → "Send to Comment Generator"
- Click floating button on Reddit pages to extract post
- Generate English comments with Chinese translations
- Multiple personas support

---

## 🌐 API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/auth/register` | POST | Register user |
| `/api/auth/login` | POST | Email login |
| `/api/auth/me` | GET | Current user |
| `/api/persona/create` | POST | Create persona |
| `/api/persona/list` | GET | List personas |
| `/api/persona/update` | PUT | Update persona |
| `/api/persona/delete` | DELETE | Delete persona |
| `/api/comment/generate` | POST | Generate comments |
| `/api/comment/use` | POST | Mark as used |

**API Docs**: http://localhost:8000/docs

---

## 🔑 API Keys

### DeepSeek (LLM)
- Get key at: https://platform.deepseek.com/api_keys
- Without it, mock comments will be used
- Default model: `deepseek-v4-flash`

---

## 🏗️ Building Executables

### Windows .exe

```cmd
cd build-tools
pip install pyinstaller
pyinstaller launcher.spec --clean --noconfirm
```

Output: `build-tools/dist/RedditCommentAssistant/`

### Shell Scripts

Already built in `build-tools/dist/`

---

## ✨ Features

- ✅ User authentication (email + password)
- ✅ Persona management (max 5 per user)
- ✅ DeepSeek AI comment generation (English only)
- ✅ Chinese translation for each comment (AI-powered)
- ✅ Comment usage tracking
- ✅ Redis caching (30 min TTL)
- ✅ Rate limiting (10 req/min)
- ✅ LLM circuit breaker
- ✅ Chrome extension with DOM parsing
- ✅ Right-click context menu to send selected text
- ✅ Multi-selector fallback