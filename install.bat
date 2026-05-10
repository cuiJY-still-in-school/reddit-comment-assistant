@echo off
setlocal

set "SCRIPT_DIR=%~dp0"
set "BACKEND_DIR=%SCRIPT_DIR%backend"

echo.
echo ==========================================
echo   Reddit Comment Assistant Installer
echo ==========================================
echo.

echo [INFO] Script directory: %SCRIPT_DIR%
echo [INFO] Backend directory: %BACKEND_DIR%
echo.

if not exist "%BACKEND_DIR%" (
    echo [ERROR] Backend directory not found: %BACKEND_DIR%
    echo Please make sure you extracted all files correctly.
    echo.
    pause
    exit /b 1
)

if not exist "%BACKEND_DIR%\requirements.txt" (
    echo [ERROR] requirements.txt not found in backend folder
    pause
    exit /b 1
)

echo ==========================================
echo   DeepSeek API Key Setup
echo ==========================================
echo.
echo You need a DeepSeek API key for AI features.
echo Get one for free at: https://platform.deepseek.com/
echo.
set /p API_KEY="Enter your DeepSeek API key (or press Enter to skip): "

echo.
echo ==========================================
echo   Port Configuration
echo ==========================================
echo.
set /p MYSQL_PORT="MySQL port [3307]: "
if "!MYSQL_PORT!"=="" set "MYSQL_PORT=3307"
set /p REDIS_PORT="Redis port [16379]: "
if "!REDIS_PORT!"=="" set "REDIS_PORT=16379"
set /p BACKEND_PORT="Backend port [8000]: "
if "!BACKEND_PORT!"=="" set "BACKEND_PORT=8000"

echo.
echo ==========================================
echo   Setup Options
echo ==========================================
echo.
echo 1. Full setup (with Docker containers)
echo 2. Backend only (skip Docker)
echo.
set /p SETUP_MODE="Choose setup mode [1]: "
if "!SETUP_MODE!"=="" set "SETUP_MODE=1"

echo.
echo [INFO] Starting setup...
echo.

:: Step 1: Check Python
echo [1/5] Checking Python...
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python not found. Please install Python 3.8+ first.
    echo Download from: https://www.python.org/downloads/
    pause
    exit /b 1
)
for /f "delims=" %%i in ('python --version 2^>^&1') do echo [OK] %%i

:: Step 2: Docker check (if selected)
if "!SETUP_MODE!"=="1" (
    echo.
    echo [2/5] Checking Docker...
    docker info >nul 2>&1
    if errorlevel 1 (
        echo [WARN] Docker not running. Please start Docker Desktop.
        echo [WARN] Skipping database setup. Make sure you have MySQL and Redis running.
    ) else (
        echo [OK] Docker is running
    )
)

:: Step 3: Setup backend
echo.
echo [3/5] Setting up backend in: %BACKEND_DIR%

cd /d "%BACKEND_DIR%" || (
    echo [ERROR] Failed to change to backend directory
    pause
    exit /b 1
)

echo [INFO] Current directory: %CD%

if not exist "venv" (
    echo [INFO] Creating Python virtual environment...
    python -m venv venv
) else (
    echo [INFO] Virtual environment already exists
)

echo [INFO] Activating virtual environment...
call venv\Scripts\activate.bat

echo [INFO] Upgrading pip...
python -m pip install --upgrade pip > nul 2>&1

echo [INFO] Installing dependencies (this may take a few minutes)...
pip install -r requirements.txt > pip_install.log 2>&1
if errorlevel 1 (
    echo [ERROR] Failed to install dependencies. Check pip_install.log for details.
    pause
    exit /b 1
)
echo [OK] Dependencies installed

:: Step 4: Create config
echo.
echo [4/5] Creating configuration file...

(
    echo # Database
    echo MYSQL_HOST=127.0.0.1
    echo MYSQL_PORT=!MYSQL_PORT!
    echo MYSQL_USER=reddit_user
    echo MYSQL_PASSWORD=reddit_password
    echo MYSQL_DATABASE=reddit_comments
    echo.
    echo # Redis
    echo REDIS_HOST=127.0.0.1
    echo REDIS_PORT=!REDIS_PORT!
    echo REDIS_DB=0
    echo.
    echo # JWT
    echo JWT_SECRET=reddit-assistant-!RANDOM!
    echo JWT_EXPIRATION_MINUTES=1440
    echo.
    echo # DeepSeek API
    echo DEEPSEEK_API_KEY=!API_KEY!
    echo DEEPSEEK_BASE_URL=https://api.deepseek.com
    echo DEEPSEEK_MODEL=deepseek-chat
    echo.
    echo # App
    echo APP_NAME=Reddit Comment Assistant
    echo DEBUG=true
) > .env

echo [OK] Configuration created: %BACKEND_DIR%\.env

:: Step 5: Start backend
echo.
echo [5/5] Starting backend server...

start "Reddit Assistant Backend" cmd /c "python -m uvicorn app.main:app --host 0.0.0.0 --port !BACKEND_PORT! >> backend.log 2>&1"

echo [INFO] Waiting for server to start...
timeout /t 5 /nobreak > nul

curl -s http://localhost:!BACKEND_PORT!/health > nul 2>&1
if errorlevel 1 (
    echo [WARN] Backend may not be fully started yet. Check backend.log for details.
) else (
    echo [OK] Backend is running at http://localhost:!BACKEND_PORT!
)

:: Chrome extension guide
echo.
echo ==========================================
echo   Chrome Extension Setup
echo ==========================================
echo.
echo To install the Chrome extension:
echo 1. Open Chrome and go to: chrome://extensions/
echo 2. Enable 'Developer mode' (top right toggle)
echo 3. Click 'Load unpacked'
echo 4. Select the folder: %SCRIPT_DIR%chrome-extension
echo.

echo ==========================================
echo   Installation Complete!
echo ==========================================
echo.
echo Backend URL:  http://localhost:!BACKEND_PORT!
echo API Docs:     http://localhost:!BACKEND_PORT!/docs
echo Health Check: http://localhost:!BACKEND_PORT!/health
echo Style Test:   http://localhost:!BACKEND_PORT!/style-test
echo.
echo Config file:  %BACKEND_DIR%\.env
echo Backend log:  %BACKEND_DIR%\backend.log
echo.
echo To stop backend: taskkill /F /IM python.exe ^>nul 2^>^&1
echo.
pause