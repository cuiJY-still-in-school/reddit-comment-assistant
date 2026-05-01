#!/bin/bash

# ============================================
# Reddit Comment Assistant - Mac Installer
# Supports: Intel (x86_64) and M1/M2/M3/M4 (arm64)
# ============================================

set -e

APP_NAME="RedditCommentAssistant"
INSTALL_DIR="$HOME/.reddit-assistant"
VENV_DIR="$INSTALL_DIR/venv"

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

log() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

detect_arch() {
    ARCH="$(uname -m)"
    if [ "$ARCH" = "x86_64" ]; then
        log "Detected: Intel Mac"
    elif [ "$ARCH" = "arm64" ]; then
        log "Detected: Apple Silicon (M1/M2/M3/M4)"
    else
        error "Unsupported architecture: $ARCH"
        exit 1
    fi
}

check_brew() {
    if ! command -v brew &> /dev/null; then
        warn "Homebrew not found. Installing..."
        /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
    fi
}

check_python() {
    log "Checking Python..."
    if command -v python3 &> /dev/null; then
        PYTHON_CMD="python3"
    elif command -v python &> /dev/null; then
        PYTHON_CMD="python"
    else
        warn "Python not found. Installing with Homebrew..."
        brew install python@3.13
        PYTHON_CMD="python3"
    fi
    PYTHON_VERSION=$($PYTHON_CMD --version 2>&1 | cut -d' ' -f2)
    log "Python version: $PYTHON_VERSION"
}

check_docker() {
    log "Checking Docker..."
    if ! docker info &> /dev/null; then
        warn "Docker not running. Please start Docker Desktop."
        open -a Docker
        log "Waiting for Docker to start..."
        for i in {1..30}; do
            if docker info &> /dev/null; then
                log "Docker is ready"
                return 0
            fi
            sleep 1
        done
        error "Docker failed to start. Please try manually."
        exit 1
    fi
    log "Docker is ready"
}

start_infrastructure() {
    log "Starting MySQL and Redis..."

    if docker ps -a --format '{{.Names}}' | grep -q "^${APP_NAME}-mysql$"; then
        docker start ${APP_NAME}-mysql 2>/dev/null || true
    else
        docker run -d \
            --name ${APP_NAME}-mysql \
            -e MYSQL_ROOT_PASSWORD=root_password \
            -e MYSQL_DATABASE=reddit_comments \
            -e MYSQL_USER=reddit_user \
            -e MYSQL_PASSWORD=reddit_password \
            -p 3307:3306 \
            mariadb:11.8 \
            --character-set-server=utf8mb4 \
            --collation-server=utf8mb4_unicode_ci
    fi

    if docker ps -a --format '{{.Names}}' | grep -q "^${APP_NAME}-redis$"; then
        docker start ${APP_NAME}-redis 2>/dev/null || true
    else
        docker run -d \
            --name ${APP_NAME}-redis \
            -p 16379:6379 \
            redis:8.0-alpine
    fi

    log "Waiting for MySQL..."
    for i in {1..30}; do
        if docker exec ${APP_NAME}-mysql mysqladmin ping -h localhost -u root -proot_password &>/dev/null; then
            log "MySQL is ready"
            break
        fi
        sleep 1
    done

    log "Initializing database..."
    docker exec ${APP_NAME}-mysql mariadb -u root -proot_password -e \
        "CREATE DATABASE IF NOT EXISTS reddit_comments CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci; \
         CREATE USER IF NOT EXISTS 'reddit_user'@'%' IDENTIFIED BY 'reddit_password'; \
         GRANT ALL PRIVILEGES ON reddit_comments.* TO 'reddit_user'@'%'; \
         FLUSH PRIVILEGES;" 2>/dev/null || true
}

setup_venv() {
    log "Setting up virtual environment..."

    if [ ! -d "$VENV_DIR" ]; then
        $PYTHON_CMD -m venv "$VENV_DIR"
    fi

    source "$VENV_DIR/bin/activate"

    log "Installing dependencies..."
    pip install --upgrade pip
    pip install fastapi uvicorn sqlalchemy aiomysql redis PyJWT bcrypt pydantic pydantic-settings python-dotenv httpx python-multipart alembic email-validator
}

create_config() {
    log "Creating configuration..."
    mkdir -p "$INSTALL_DIR"

    RANDOM_KEY=$(date +%s)$(head /dev/urandom | tr -dc '0-9' | head -c 10)

    cat > "$INSTALL_DIR/.env" << EOF
MYSQL_HOST=127.0.0.1
MYSQL_PORT=3307
MYSQL_USER=reddit_user
MYSQL_PASSWORD=reddit_password
MYSQL_DATABASE=reddit_comments
REDIS_HOST=127.0.0.1
REDIS_PORT=16379
REDIS_DB=0
JWT_SECRET_KEY=reddit-assistant-jwt-secret-$RANDOM_KEY
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=1440
DEEPSEEK_API_KEY=
DEEPSEEK_API_BASE=https://api.deepseek.com
DEEPSEEK_MODEL=deepseek-chat
DEEPSEEK_TIMEOUT=10
GOOGLE_CLIENT_ID=
GOOGLE_CLIENT_SECRET=
RATE_LIMIT_PER_MINUTE=10
LLM_CONCURRENT_LIMIT=5
CIRCUIT_BREAKER_THRESHOLD=5
CIRCUIT_BREAKER_RECOVERY_SECONDS=60
APP_NAME=Reddit Comment Assistant
DEBUG=false
EOF
}

launch_app() {
    log "Launching Reddit Comment Assistant..."
    source "$VENV_DIR/bin/activate"
    cd "$INSTALL_DIR"

    SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

    if [ ! -d "$INSTALL_DIR/app" ]; then
        log "Installing application files..."
        cp -r "$SCRIPT_DIR/../app" "$INSTALL_DIR/"
    fi

    echo ""
    echo "=========================================="
    echo "  Reddit Comment Assistant"
    echo "=========================================="
    echo ""
    echo "  API Server: http://localhost:8000"
    echo "  API Docs:   http://localhost:8000/docs"
    echo ""
    echo "  Press Ctrl+C to stop"
    echo "=========================================="
    echo ""

    python -m uvicorn app.main:app --host 0.0.0.0 --port 8000
}

main() {
    echo ""
    echo "=========================================="
    echo "  Reddit Comment Assistant"
    echo "  Mac Installer & Launcher"
    echo "=========================================="
    echo ""

    detect_arch
    check_brew
    check_python
    check_docker
    start_infrastructure
    setup_venv
    create_config
    launch_app
}

trap 'docker stop ${APP_NAME}-mysql ${APP_NAME}-redis 2>/dev/null' EXIT

main "$@"
