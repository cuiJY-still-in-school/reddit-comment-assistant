@echo off
setlocal enabledelayedexpansion

set APP_NAME=RedditCommentAssistant
set INSTALL_DIR=%USERPROFILE%\.reddit-assistant
set VENV_DIR=%INSTALL_DIR%\venv

echo.
echo ==========================================
echo   Reddit Comment Assistant
echo   Installer ^& Launcher for Windows
echo ==========================================
echo.

:: Detect architecture
echo [INFO] Detecting system...
if "%PROCESSOR_ARCHITECTURE%"=="x86" (
    if defined PROCESSOR_ARCHITEW6432 (
        set ARCH=x64
    ) else (
        set ARCH=x86
    )
) else (
    set ARCH=x64
)
echo [INFO] Architecture: %ARCH%

:: Check admin rights
net session >nul 2>&1
if %errorLevel% neq 0 (
    echo [WARN] Some operations require administrator rights.
    echo [WARN] Please run as administrator if installation fails.
)

:: Check Python
echo [INFO] Checking Python...
python --version >nul 2>&1
if errorlevel 1 (
    echo [INFO] Python not found. Please install Python 3.10+ from python.org
    echo [INFO] Then run this script again.
    pause
    exit /b 1
)

for /f "delims=" %%i in ('python --version 2^>^&1') do set PYTHON_VERSION=%%i
echo [INFO] Python: !PYTHON_VERSION!

:: Check Docker
echo [INFO] Checking Docker...
docker info >nul 2>&1
if errorlevel 1 (
    echo [WARN] Docker not found or not running.
    echo [INFO] Installing Docker...
    powershell -Command "Start-Process powershell -Verb RunAs -Wait -ArgumentList '-Commandirm https://get.docker.com ^| iex'"
)

:: Start Docker if not running
docker info >nul 2>&1
if errorlevel 1 (
    echo [INFO] Starting Docker Desktop...
    start "" "C:\Program Files\Docker\Docker\Docker Desktop.exe"
    echo [INFO] Waiting for Docker to start...
    timeout /t 15 /nobreak >nul
)

:: Start MySQL container
echo [INFO] Starting MySQL container...
docker run -d --name %APP_NAME%-mysql ^
    -e MYSQL_ROOT_PASSWORD=root_password ^
    -e MYSQL_DATABASE=reddit_comments ^
    -e MYSQL_USER=reddit_user ^
    -e MYSQL_PASSWORD=reddit_password ^
    -p 3307:3306 ^
    mariadb:11.8 ^
    --character-set-server=utf8mb4 ^
    --collation-server=utf8mb4_unicode_ci >nul 2>&1

:: Start Redis container
echo [INFO] Starting Redis container...
docker run -d --name %APP_NAME%-redis -p 16379:6379 redis:8.0-alpine >nul 2>&1

:: Wait for MySQL
echo [INFO] Waiting for MySQL to be ready...
for /L %%i in (1,1,30) do (
    docker exec %APP_NAME%-mysql mysqladmin ping -h localhost -u root -proot_password >nul 2>&1
    if not errorlevel 1 goto :mysql_ready
    timeout /t 1 /nobreak >nul
)
:mysql_ready
echo [INFO] MySQL is ready

:: Initialize database
echo [INFO] Initializing database...
docker exec %APP_NAME%-mysql mariadb -u root -proot_password -e "CREATE DATABASE IF NOT EXISTS reddit_comments CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci; CREATE USER IF NOT EXISTS 'reddit_user'@'%%' IDENTIFIED BY 'reddit_password'; GRANT ALL PRIVILEGES ON reddit_comments.* TO 'reddit_user'@'%%'; FLUSH PRIVILEGES;" >nul 2>&1

:: Create installation directory
echo [INFO] Setting up installation directory...
if not exist "%INSTALL_DIR%" mkdir "%INSTALL_DIR%"
if not exist "%VENV_DIR%" (
    echo [INFO] Creating virtual environment...
    python -m venv "%VENV_DIR%"
)

:: Activate virtual environment and install dependencies
echo [INFO] Installing dependencies...
call "%VENV_DIR%\Scripts\activate.bat"
pip install --upgrade pip >nul 2>&1
pip install fastapi uvicorn sqlalchemy aiomysql redis PyJWT bcrypt pydantic pydantic-settings python-dotenv httpx python-multipart alembic email-validator >nul 2>&1

:: Create .env file
echo [INFO] Creating configuration...
set RANDOM_KEY=%RANDOM%%RANDOM%%RANDOM%
(
echo MYSQL_HOST=127.0.0.1
echo MYSQL_PORT=3307
echo MYSQL_USER=reddit_user
echo MYSQL_PASSWORD=reddit_password
echo MYSQL_DATABASE=reddit_comments
echo REDIS_HOST=127.0.0.1
echo REDIS_PORT=16379
echo REDIS_DB=0
echo JWT_SECRET_KEY=reddit-assistant-jwt-secret-key-%RANDOM_KEY%
echo JWT_ACCESS_TOKEN_EXPIRE_MINUTES=1440
echo DEEPSEEK_API_KEY=
echo DEEPSEEK_API_BASE=https://api.deepseek.com
echo DEEPSEEK_MODEL=deepseek-chat
echo DEEPSEEK_TIMEOUT=10
echo GOOGLE_CLIENT_ID=
echo GOOGLE_CLIENT_SECRET=
echo RATE_LIMIT_PER_MINUTE=10
echo LLM_CONCURRENT_LIMIT=5
echo CIRCUIT_BREAKER_THRESHOLD=5
echo CIRCUIT_BREAKER_RECOVERY_SECONDS=60
echo APP_NAME=Reddit Comment Assistant
echo DEBUG=false
) > "%INSTALL_DIR%\.env"

:: Copy app files
echo [INFO] Copying application files...
xcopy /E /Y /Q "%~dp0app" "%INSTALL_DIR%\app\" >nul 2>&1
xcopy /Y /Q "%~dp0requirements.txt" "%INSTALL_DIR%\" >nul 2>&1

:: Launch
echo.
echo ==========================================
echo   Reddit Comment Assistant
echo ==========================================
echo.
echo   API Server: http://localhost:8000
echo   API Docs:   http://localhost:8000/docs
echo.
echo   Press Ctrl+C to stop
echo ==========================================
echo.

cd /d "%INSTALL_DIR%"
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000

:end
endlocal
