#!/bin/bash

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Default values
DEEPSEEK_API_KEY=""
MYSQL_PORT=3307
REDIS_PORT=16379
BACKEND_PORT=8000

log_info() { echo -e "${BLUE}[INFO]${NC} $1"; }
log_success() { echo -e "${GREEN}[SUCCESS]${NC} $1"; }
log_warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }

header() {
    echo ""
    echo "=========================================="
    echo "  Reddit Comment Assistant Installer"
    echo "=========================================="
    echo ""
}

check_python() {
    log_info "Checking Python version..."
    if command -v python3 &> /dev/null; then
        PYTHON_VERSION=$(python3 --version 2>&1 | awk '{print $2}')
        log_success "Python $PYTHON_VERSION found"
    else
        log_error "Python 3 is not installed"
        echo "Please install Python 3.8 or later: https://www.python.org/downloads/"
        exit 1
    fi
}

check_docker() {
    log_info "Checking Docker..."
    if command -v docker &> /dev/null; then
        if docker info &> /dev/null; then
            log_success "Docker is running"
        else
            log_warn "Docker is installed but not running"
            echo "Please start Docker Desktop or docker daemon"
        fi
    else
        log_warn "Docker not found (optional - for local database)"
        echo "If you don't have MySQL/Redis, you can use cloud services"
    fi
}

check_git() {
    log_info "Checking Git..."
    if command -v git &> /dev/null; then
        log_success "Git found"
    else
        log_warn "Git not found (optional)"
    fi
}

get_deepseek_key() {
    echo ""
    echo "=========================================="
    echo "  DeepSeek API Key Setup"
    echo "=========================================="
    echo ""
    echo "You need a DeepSeek API key to use the AI features."
    echo "Get one for free at: https://platform.deepseek.com/"
    echo ""
    read -p "Enter your DeepSeek API key (or press Enter to skip for now): " DEEPSEEK_API_KEY

    if [ -z "$DEEPSEEK_API_KEY" ]; then
        log_warn "No API key provided. You can add it later in backend/.env"
    else
        log_success "API key received"
    fi
}

get_ports() {
    echo ""
    echo "=========================================="
    echo "  Port Configuration"
    echo "=========================================="
    echo ""

    read -p "MySQL port [${MYSQL_PORT}]: " INPUT_PORT
    MYSQL_PORT=${INPUT_PORT:-$MYSQL_PORT}

    read -p "Redis port [${REDIS_PORT}]: " INPUT_PORT
    REDIS_PORT=${INPUT_PORT:-$REDIS_PORT}

    read -p "Backend port [${BACKEND_PORT}]: " INPUT_PORT
    BACKEND_PORT=${INPUT_PORT:-$BACKEND_PORT}

    log_success "Ports configured"
}

setup_backend() {
    log_info "Setting up backend..."

    cd backend

    # Create virtual environment if it doesn't exist
    if [ ! -d "venv" ]; then
        log_info "Creating Python virtual environment..."
        python3 -m venv venv
        log_success "Virtual environment created"
    fi

    # Activate virtual environment
    log_info "Activating virtual environment..."
    source venv/bin/activate

    # Install dependencies
    log_info "Installing Python dependencies..."
    pip install --upgrade pip
    pip install -r requirements.txt
    log_success "Dependencies installed"

    # Create .env file
    log_info "Creating configuration file..."
    cat > .env << EOF
# Database
MYSQL_HOST=127.0.0.1
MYSQL_PORT=${MYSQL_PORT}
MYSQL_USER=reddit_user
MYSQL_PASSWORD=reddit_password
MYSQL_DATABASE=reddit_comments

# Redis
REDIS_HOST=127.0.0.1
REDIS_PORT=${REDIS_PORT}
REDIS_DB=0

# JWT
JWT_SECRET=reddit-assistant-dev-secret-$(date +%s)
JWT_EXPIRATION_MINUTES=1440

# DeepSeek API
DEEPSEEK_API_KEY=${DEEPSEEK_API_KEY}
DEEPSEEK_BASE_URL=https://api.deepseek.com
DEEPSEEK_MODEL=deepseek-chat

# App
APP_NAME=Reddit Comment Assistant
DEBUG=true
EOF
    log_success "Configuration file created"

    cd ..
}

start_database() {
    log_info "Checking database services..."

    # Check if MySQL container exists
    if docker ps -a --format '{{.Names}}' | grep -q "reddit-mysql"; then
        if ! docker ps --format '{{.Names}}' | grep -q "reddit-mysql"; then
            log_info "Starting MySQL container..."
            docker start reddit-mysql
        fi
        log_success "MySQL is ready"
    else
        log_warn "MySQL container 'reddit-mysql' not found"
        echo "Please ensure MySQL is running and accessible"
    fi

    # Check if Redis container exists
    if docker ps -a --format '{{.Names}}' | grep -q "reddit-redis"; then
        if ! docker ps --format '{{.Names}}' | grep -q "reddit-redis"; then
            log_info "Starting Redis container..."
            docker start reddit-redis
        fi
        log_success "Redis is ready"
    else
        log_warn "Redis container 'reddit-redis' not found"
        echo "Please ensure Redis is running and accessible"
    fi
}

start_backend() {
    log_info "Starting backend server..."

    cd backend
    source venv/bin/activate

    # Start uvicorn in background
    nohup python -m uvicorn app.main:app --host 0.0.0.0 --port ${BACKEND_PORT} > backend.log 2>&1 &
    BACKEND_PID=$!

    # Wait for backend to start
    sleep 3

    # Check if backend is running
    if curl -s http://localhost:${BACKEND_PORT}/health > /dev/null 2>&1; then
        log_success "Backend is running at http://localhost:${BACKEND_PORT}"
    else
        log_warn "Backend may not be fully started yet"
    fi

    cd ..
}

setup_chrome_extension() {
    log_info "Setting up Chrome extension..."

    EXTENSION_DIR="chrome-extension"

    if [ ! -d "$EXTENSION_DIR" ]; then
        log_error "Chrome extension directory not found"
        return 1
    fi

    echo ""
    echo "=========================================="
    echo "  Chrome Extension Setup"
    echo "=========================================="
    echo ""
    echo "To install the Chrome extension:"
    echo "1. Open Chrome and go to: chrome://extensions/"
    echo "2. Enable 'Developer mode' (top right toggle)"
    echo "3. Click 'Load unpacked'"
    echo "4. Select the '${EXTENSION_DIR}' folder"
    echo ""
    echo "Note: The extension loads files from src/ directory"
    echo "For production, run: cd ${EXTENSION_DIR} && npm run build"
    echo ""

    log_success "Chrome extension setup instructions provided"
}

final_summary() {
    echo ""
    echo "=========================================="
    echo "  Installation Complete!"
    echo "=========================================="
    echo ""
    echo "Backend:     http://localhost:${BACKEND_PORT}"
    echo "API Docs:    http://localhost:${BACKEND_PORT}/docs"
    echo "Health:      http://localhost:${BACKEND_PORT}/health"
    echo "Test Page:   http://localhost:${BACKEND_PORT}/style-test"
    echo ""
    echo "Chrome Extension:"
    echo "  1. Open chrome://extensions/"
    echo "  2. Enable Developer mode"
    echo "  3. Click Load unpacked → select chrome-extension/"
    echo ""
    echo "To stop backend: pkill -f uvicorn"
    echo "To start backend: cd backend && source venv/bin/activate && python -m uvicorn app.main:app --port ${BACKEND_PORT}"
    echo ""
}

# Main installation flow
main() {
    header

    check_python
    check_docker
    check_git

    echo ""
    read -p "Continue with installation? [Y/n]: " CONFIRM
    CONFIRM=${CONFIRM:-Y}
    if [[ "$CONFIRM" =~ ^[Nn] ]]; then
        log_info "Installation cancelled"
        exit 0
    fi

    get_deepseek_key
    get_ports
    setup_backend
    start_database
    start_backend
    setup_chrome_extension
    final_summary
}

main "$@"