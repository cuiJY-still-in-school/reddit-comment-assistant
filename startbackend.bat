@echo off
setlocal

echo.
echo ==========================================
echo   Reddit Comment Assistant - Backend
echo ==========================================
echo.

set "SCRIPT_DIR=%~dp0"
set "BACKEND_DIR=%SCRIPT_DIR%backend"

if not exist "%BACKEND_DIR%" (
    echo [ERROR] Backend directory not found: %BACKEND_DIR%
    echo Please make sure you extracted all files correctly.
    pause
    exit /b 1
)

cd /d "%BACKEND_DIR%"

:: Create venv if not exists
if not exist "venv" (
    echo [INFO] Creating Python virtual environment...
    python -m venv venv
)

:: Activate venv
echo [INFO] Activating virtual environment...
call venv\Scripts\activate.bat

:: Install dependencies
echo [INFO] Installing dependencies...
pip install --quiet --upgrade pip
pip install --quiet -r requirements.txt
if errorlevel 1 (
    echo [INFO] Trying individual packages...
    pip install fastapi uvicorn sqlalchemy aiomysql redis PyJWT bcrypt pydantic pydantic-settings python-dotenv httpx python-multipart email-validator passlib
)

:: Check .env file
if not exist ".env" (
    echo [INFO] Creating default .env file...
    (
        echo MYSQL_HOST=127.0.0.1
        echo MYSQL_PORT=3307
        echo MYSQL_USER=reddit_user
        echo MYSQL_PASSWORD=reddit_password
        echo MYSQL_DATABASE=reddit_comments
        echo REDIS_HOST=127.0.0.1
        echo REDIS_PORT=16379
        echo REDIS_DB=0
        echo JWT_SECRET=reddit-assistant-dev-secret
        echo JWT_EXPIRATION_MINUTES=1440
        echo DEEPSEEK_API_KEY=
        echo DEEPSEEK_BASE_URL=https://api.deepseek.com
        echo DEEPSEEK_MODEL=deepseek-chat
        echo APP_NAME=Reddit Comment Assistant
        echo DEBUG=true
    ) > .env
)

:: Check API key
findstr /C:"DEEPSEEK_API_KEY=" .env | findstr /v "#" >nul
if errorlevel 1 (
    echo.
    echo ==========================================
    echo   DeepSeek API Key Required
    echo ==========================================
    echo Please add your DeepSeek API key to backend\.env
    echo Get your API key at: https://platform.deepseek.com/
    echo.
)

echo [INFO] Starting backend server...
echo [INFO] Backend: http://localhost:8000
echo [INFO] API Docs: http://localhost:8000/docs
echo [INFO] Style Test: http://localhost:8000/style-test
echo.
echo Press Ctrl+C to stop
echo ==========================================
echo.

python -m uvicorn app.main:app --host 0.0.0.0 --port 8000

endlocal