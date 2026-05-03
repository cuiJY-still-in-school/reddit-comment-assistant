# Reddit Comment Assistant

AI-powered Reddit comment generation system with Chrome extension.

---

## 🚀 Quick Start - Interactive Setup Wizard

```bash
# Linux / Mac
chmod +x build-tools/setup_wizard.py
python3 build-tools/setup_wizard.py

# Windows
python build-tools/setup_wizard.py
```

The wizard will guide you through:
1. **Database Setup** - Starts MySQL & Redis via Docker
2. **Python Environment** - Creates venv and installs packages
3. **API Keys** - Optional: DeepSeek API for AI generation
4. **Launch** - Starts the API server

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
│   ├── setup_wizard.py    # ⭐ Interactive setup wizard
│   ├── launcher.py        # PyInstaller launcher
│   ├── install.sh         # Linux installer
│   ├── install-mac.sh     # Mac installer
│   ├── install.bat        # Windows installer
│   └── dist/              # Built executables
└── docker-compose.yml     # MySQL + Redis
```

---

## 🔧 Development Setup

### 1. Setup Wizard (Recommended)

```bash
python3 build-tools/setup_wizard.py
```

### 2. Manual Setup

```bash
# Start infrastructure
docker compose up -d mysql redis

# Install dependencies
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Run
uvicorn app.main:app --port 8000
```

### 3. Chrome Extension

1. Open `chrome://extensions/`
2. Enable **Developer mode**
3. Click **Load unpacked**
4. Select `chrome-extension/` folder

---

## 🌐 API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/auth/register` | POST | Register user |
| `/api/auth/login` | POST | Email login |
| `/api/auth/cookie-login` | POST | Reddit cookie login |
| `/api/auth/login/google` | POST | Google OAuth |
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

- ✅ User authentication (email + Reddit cookie)
- ✅ Persona management (max 5 per user)
- ✅ DeepSeek AI comment generation (English only)
- ✅ Comment usage tracking
- ✅ Redis caching (30 min TTL)
- ✅ Rate limiting (10 req/min)
- ✅ LLM circuit breaker
- ✅ Chrome extension with DOM parsing
- ✅ Multi-selector fallback
- ✅ Interactive setup wizard
