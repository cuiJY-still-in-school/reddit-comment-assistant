# Reddit Comment Assistant

AI-powered Reddit comment generation system with Chrome extension.

---

## 🚀 Quick Start

### Linux / macOS

```bash
# 1. Clone and install
git clone https://github.com/cuiJY-still-in-school/reddit-comment-assistant.git
cd reddit-comment-assistant
chmod +x install.sh
./install.sh

# 2. Or manual setup
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# 3. Configure (edit .env with your DeepSeek API key)
# DEEPSEEK_API_KEY=your-key-here

# 4. Start backend
python -m uvicorn app.main:app --port 8000
```

### Windows

```cmd
# 1. Clone or download the project
# 2. Run the installer
install.bat

# Or manual setup
cd backend
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
python -m uvicorn app.main:app --port 8000
```

---

## 📥 Installation Scripts

| Platform | File | Description |
|----------|------|-------------|
| Linux/macOS | `install.sh` | Interactive installer with all setup steps |
| Windows | `install.bat` | Interactive Windows installer |

Run the installer and it will guide you through:
1. DeepSeek API key setup
2. Port configuration (MySQL, Redis, Backend)
3. Python environment setup
4. Configuration file creation
5. Database container startup
6. Backend server startup
7. Chrome extension installation guide

---

## 📁 Project Structure

```
reddit-comment-assistant/
├── backend/                    # FastAPI Backend
│   ├── app/
│   │   ├── main.py            # FastAPI entry point
│   │   ├── api/               # API routes (auth, persona, comment, style)
│   │   ├── core/              # Config, security, response utilities
│   │   ├── dao/               # Data access layer
│   │   ├── models/            # SQLAlchemy models
│   │   ├── schemas/            # Pydantic schemas (DTOs)
│   │   ├── services/           # Business logic layer
│   │   └── utils/             # Cache, rate limiter, etc.
│   ├── config/                # Environment templates
│   ├── database/              # Database connection
│   └── requirements.txt       # Python dependencies
│
├── chrome-extension/           # Chrome Extension
│   ├── src/                   # TypeScript source files
│   │   ├── config/           # Environment configuration
│   │   ├── popup/            # Popup UI
│   │   ├── content/          # Content script
│   │   └── background/       # Background service worker
│   ├── public/                # Static assets
│   ├── package.json          # NPM dependencies
│   ├── vite.config.ts        # Vite build config
│   └── tsconfig.json         # TypeScript config
│
├── launcher-page/             # Test pages
│   └── style-test.html       # Style learning test page
│
├── install.sh                 # Linux/macOS installer
├── install.bat                # Windows installer
└── README.md
```

---

## 🌐 Architecture

### Backend Layers

```
API Layer (api/)
    ↓
Service Layer (services/)
    ↓
DAO Layer (dao/)              ← Data access, no business logic
    ↓
Model Layer (models/)          ← SQLAlchemy ORM models
```

### Key Components

| Layer | Purpose |
|-------|---------|
| `api/` | HTTP request handling, input validation via Pydantic |
| `core/` | Shared utilities (Response, Security, Config) |
| `services/` | Business logic, validation, orchestration |
| `dao/` | Database CRUD operations only |
| `models/` | Database table definitions |
| `schemas/` | Data transfer objects for API |

---

## 🔧 Chrome Extension Setup

1. Open `chrome://extensions/`
2. Enable **Developer mode** (top right toggle)
3. Click **Load unpacked**
4. Select `chrome-extension/` folder

**Features:**
- Generate comments for Reddit posts
- Learn your writing style
- Multiple persona support
- English comments with Chinese translations

---

## 🌐 API Endpoints

### Authentication
| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/auth/register` | POST | Register new user |
| `/api/auth/login` | POST | Email login |
| `/api/auth/me` | GET | Get current user info |

### Persona
| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/persona/create` | POST | Create persona |
| `/api/persona/list` | GET | List user's personas |
| `/api/persona/update` | PUT | Update persona |
| `/api/persona/delete` | DELETE | Delete persona |

### Comment Generation
| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/comment/generate` | POST | Generate comment with AI |
| `/api/comment/use` | POST | Mark comment as used |

### Style Learning
| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/style/posts` | GET | Get Reddit posts |
| `/api/style/sample` | POST | Submit style sample |
| `/api/style/profile` | GET | Get user's style profile |
| `/api/style/analyze` | POST | Analyze writing style |
| `/api/style/samples` | GET | List user's samples |

**API Docs**: http://localhost:8000/docs

---

## 🔑 API Keys

### DeepSeek (LLM)
- Get key at: https://platform.deepseek.com/api_keys
- Required for AI comment generation
- Default model: `deepseek-chat`

---

## ✨ Features

- ✅ User authentication (email + password)
- ✅ Persona management (max 5 per user)
- ✅ DeepSeek AI comment generation
- ✅ Chinese translation for comments
- ✅ Style learning (analyze your writing style)
- ✅ Comment usage tracking
- ✅ Redis caching
- ✅ Rate limiting
- ✅ LLM circuit breaker
- ✅ Chrome extension with Reddit DOM parsing
- ✅ Right-click context menu
- ✅ Multi-selector fallback

---

## 📋 Unified Response Format

All API responses follow this structure:

```json
{
    "success": true,
    "code": 0,
    "message": "success",
    "data": { ... },
    "timestamp": 1778326646076
}
```

| Field | Type | Description |
|-------|------|-------------|
| `success` | boolean | Whether the request succeeded |
| `code` | integer | Business code (0 = success, others = error) |
| `message` | string | Human-readable message |
| `data` | object | Response data (null on error) |
| `timestamp` | integer | Unix timestamp in milliseconds |

---

## 🛠️ Development

### Run Backend

```bash
cd backend
source venv/bin/activate  # or venv\Scripts\activate on Windows
python -m uvicorn app.main:app --reload --port 8000
```

### Test Style Learning

Open http://localhost:8000/style-test after starting the backend.

### Build Chrome Extension

```bash
cd chrome-extension
npm install
npm run build  # outputs to dist/
```

---

## 📝 License

MIT