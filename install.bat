@echo off
setlocal enabledelayedexpansion

:: Colors (Windows cmd doesn't support colors directly, use trick)
set "ESC="
set "GREEN=[92m"
set "YELLOW=[93m"
set "BLUE=[94m"
set "RED=[91m"
set "NC=[0m"

:: Default values
set "DEEPSEEK_API_KEY="
set "MYSQL_PORT=3307"
set "REDIS_PORT=16379"
set "BACKEND_PORT=8000"

:header
cls
echo.
echo ==========================================
echo   Reddit Comment Assistant Installer
echo ==========================================
echo.
goto :eof

:log_info
echo [INFO] %~1
goto :eof

:log_success
echo [SUCCESS] %~1
goto :eof

:log_warn
echo [WARN] %~1
goto :eof

:log_error
echo [ERROR] %~1
goto :eof

:check_python
call :log_info "Checking Python version..."
python --version >nul 2>&1
if errorlevel 1 (
    call :log_error "Python is not installed"
    echo Please install Python 3.8 or later: https://www.python.org/downloads/
    pause
    exit /b 1
)
for /f "delims=" %%i in ('python --version 2^>^&1') do set "PYTHON_VERSION=%%i"
call :log_success "Python found: !PYTHON_VERSION!"
goto :eof

:check_docker
call :log_info "Checking Docker..."
docker info >nul 2>&1
if errorlevel 1 (
    call :log_warn "Docker is not running or not installed"
    echo If you don't have MySQL/Redis, you can use cloud services
) else (
    call :log_success "Docker is running"
)
goto :eof

:get_deepseek_key
cls
call :header
echo ==========================================
echo   DeepSeek API Key Setup
echo ==========================================
echo.
echo You need a DeepSeek API key to use the AI features.
echo Get one for free at: https://platform.deepseek.com/
echo.
set /p DEEPSEEK_API_KEY="Enter your DeepSeek API key (or press Enter to skip): "
if "!DEEPSEEK_API_KEY!"=="" (
    call :log_warn "No API key provided. You can add it later in backend\.env"
) else (
    call :log_success "API key received"
)
goto :eof

:get_ports
cls
call :header
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
call :log_success "Ports configured"
goto :eof

:setup_backend
call :log_info "Setting up backend..."
cd /d "%~dp0backend"

call :log_info "Creating Python virtual environment..."
python -m venv venv

call :log_info "Activating virtual environment..."
call venv\Scripts\activate.bat

call :log_info "Installing Python dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

call :log_info "Creating configuration file..."
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
    echo JWT_SECRET=reddit-assistant-dev-secret-%RANDOM%
    echo JWT_EXPIRATION_MINUTES=1440
    echo.
    echo # DeepSeek API
    echo DEEPSEEK_API_KEY=!DEEPSEEK_API_KEY!
    echo DEEPSEEK_BASE_URL=https://api.deepseek.com
    echo DEEPSEEK_MODEL=deepseek-chat
    echo.
    echo # App
    echo APP_NAME=Reddit Comment Assistant
    echo DEBUG=true
) > .env

call :log_success "Configuration file created"
cd /d "%~dp0"
goto :eof

:start_database
call :log_info "Checking database services..."

docker ps -a --format "{{.Names}}" | findstr /C:"reddit-mysql" >nul
if not errorlevel 1 (
    docker ps --format "{{.Names}}" | findstr /C:"reddit-mysql" >nul
    if errorlevel 1 (
        call :log_info "Starting MySQL container..."
        docker start reddit-mysql
    )
    call :log_success "MySQL is ready"
) else (
    call :log_warn "MySQL container 'reddit-mysql' not found"
)

docker ps -a --format "{{.Names}}" | findstr /C:"reddit-redis" >nul
if not errorlevel 1 (
    docker ps --format "{{.Names}}" | findstr /C:"reddit-redis" >nul
    if errorlevel 1 (
        call :log_info "Starting Redis container..."
        docker start reddit-redis
    )
    call :log_success "Redis is ready"
) else (
    call :log_warn "Redis container 'reddit-redis' not found"
)
goto :eof

:start_backend
call :log_info "Starting backend server..."

cd /d "%~dp0backend"
call venv\Scripts\activate.bat

start /B cmd /c "python -m uvicorn app.main:app --host 0.0.0.0 --port %BACKEND_PORT% > backend.log 2>&1"

call :log_info "Waiting for backend to start..."
timeout /t 3 /nobreak >nul

curl -s http://localhost:%BACKEND_PORT%/health >nul 2>&1
if not errorlevel 1 (
    call :log_success "Backend is running at http://localhost:%BACKEND_PORT%"
) else (
    call :log_warn "Backend may not be fully started yet"
)

cd /d "%~dp0"
goto :eof

:setup_chrome_extension
cls
call :header
echo ==========================================
echo   Chrome Extension Setup
echo ==========================================
echo.
echo To install the Chrome extension:
echo 1. Open Chrome and go to: chrome://extensions/
echo 2. Enable 'Developer mode' (top right toggle)
echo 3. Click 'Load unpacked'
echo 4. Select the 'chrome-extension' folder
echo.
echo Note: The extension uses files from src/ directory
echo For production, run: cd chrome-extension ^&^& npm run build
echo.
call :log_success "Chrome extension setup instructions provided"
pause
goto :eof

:final_summary
cls
call :header
echo ==========================================
echo   Installation Complete!
echo ==========================================
echo.
echo Backend:     http://localhost:%BACKEND_PORT%
echo API Docs:    http://localhost:%BACKEND_PORT%/docs
echo Health:      http://localhost:%BACKEND_PORT%/health
echo Test Page:   http://localhost:%BACKEND_PORT%/style-test
echo.
echo Chrome Extension:
echo   1. Open chrome://extensions/
echo   2. Enable Developer mode
echo   3. Click Load unpacked ^> select chrome-extension/
echo.
echo To stop backend: taskkill /F /IM python.exe 2^>nul ^&^& taskkill /F /IM uvicorn.exe 2^>nul
echo.
pause
goto :eof

:main
call :header

call :check_python
call :check_docker

echo.
set /p CONFIRM="Continue with installation? [Y/n]: "
if /i "!CONFIRM!"=="n" (
    call :log_info "Installation cancelled"
    pause
    exit /b 0
)

call :get_deepseek_key
call :get_ports
call :setup_backend
call :start_database
call :start_backend
call :setup_chrome_extension
call :final_summary

:end
endlocal
exit /b 0

:: Start main
goto :main