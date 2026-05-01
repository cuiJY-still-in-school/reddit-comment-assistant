#!/bin/bash

# ============================================
# Reddit Comment Assistant - Installer & Launcher
# Supports: Linux (x86_64, arm64), Mac (Intel, M1/M2/M3/M4)
# ============================================

set -e

APP_NAME="RedditCommentAssistant"
INSTALL_DIR="$HOME/.reddit-assistant"
VENV_DIR="$INSTALL_DIR/venv"
LOG_FILE="$INSTALL_DIR/install.log"

# Colors
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

detect_os() {
    OS="$(uname -s)"
    ARCH="$(uname -m)"

    case "$OS" in
        Linux*)
            OS_NAME="linux"
            if [ "$ARCH" = "x86_64" ]; then
                ARCH_NAME="x86_64"
            elif [ "$ARCH" = "aarch64" ] || [ "$ARCH" = "arm64" ]; then
                ARCH_NAME="arm64"
            else
                error "Unsupported architecture: $ARCH"
                exit 1
            fi
            ;;
        Darwin*)
            OS_NAME="mac"
            if [ "$ARCH" = "x86_64" ]; then
                ARCH_NAME="intel"
            elif [ "$ARCH" = "arm64" ]; then
                ARCH_NAME="m1"
            else
                error "Unsupported architecture: $ARCH"
                exit 1
            fi
            ;;
        *)
            error "Unsupported OS: $OS"
            exit 1
            ;;
    esac

    log "Detected: $OS_NAME ($ARCH_NAME)"
}

check_docker() {
    log "Checking Docker..."

    if ! command -v docker &> /dev/null; then
        warn "Docker not found. Installing Docker..."

        if [ "$OS_NAME" = "linux" ]; then
            curl -fsSL https://get.docker.com | sh
            sudo usermod -aG docker $USER
        elif [ "$OS_NAME" = "mac" ]; then
            echo "Please install Docker Desktop from https://docker.com/products/docker-desktop"
            echo "Then run this script again."
            exit 1
        fi
    fi

    if ! docker info &> /dev/null; then
        warn "Docker is not running. Starting Docker..."
        if [ "$OS_NAME" = "linux" ]; then
            sudo systemctl start docker
        elif [ "$OS_NAME" = "mac" ]; then
            open -a Docker
        fi
        sleep 3
    fi

    log "Docker is ready"
}

start_infrastructure() {
    log "Starting MySQL and Redis via Docker..."

    # Check if containers already exist
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
            --collation-server=utf8mb4_unicode_ci \
            > /dev/null 2>&1
    fi

    if docker ps -a --format '{{.Names}}' | grep -q "^${APP_NAME}-redis$"; then
        docker start ${APP_NAME}-redis 2>/dev/null || true
    else
        docker run -d \
            --name ${APP_NAME}-redis \
            -p 16379:6379 \
            redis:8.0-alpine \
            > /dev/null 2>&1
    fi

    # Wait for MySQL to be ready
    log "Waiting for MySQL to be ready..."
    for i in {1..30}; do
        if docker exec ${APP_NAME}-mysql mysqladmin ping -h localhost -u root -proot_password &>/dev/null; then
            log "MySQL is ready"
            break
        fi
        sleep 1
    done

    # Initialize database
    log "Initializing database..."
    docker exec ${APP_NAME}-mysql mariadb -u root -proot_password -e \
        "CREATE DATABASE IF NOT EXISTS reddit_comments CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci; \
         CREATE USER IF NOT EXISTS 'reddit_user'@'%' IDENTIFIED BY 'reddit_password'; \
         GRANT ALL PRIVILEGES ON reddit_comments.* TO 'reddit_user'@'%'; \
         FLUSH PRIVILEGES;" 2>/dev/null || true

    log "Infrastructure ready"
}

check_python() {
    log "Checking Python..."

    if command -v python3 &> /dev/null; then
        PYTHON_CMD="python3"
    elif command -v python &> /dev/null; then
        PYTHON_CMD="python"
    else
        warn "Python not found. Installing Python..."

        if [ "$OS_NAME" = "linux" ]; then
            if command -v apt-get &> /dev/null; then
                sudo apt-get update && sudo apt-get install -y python3 python3-venv python3-pip
            elif command -v yum &> /dev/null; then
                sudo yum install -y python3 python3-venv
            elif command -v pacman &> /dev/null; then
                sudo pacman -Sy --noconfirm python python-pip
            fi
        elif [ "$OS_NAME" = "mac" ]; then
            /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
            brew install python@3.13
        fi

        PYTHON_CMD="python3"
    fi

    PYTHON_VERSION=$($PYTHON_CMD --version | cut -d' ' -f2 | cut -d'.' -f1,2)
    log "Python version: $PYTHON_VERSION"
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

    log "Dependencies installed"
}

create_env_file() {
    log "Creating configuration..."

    mkdir -p "$INSTALL_DIR"

    cat > "$INSTALL_DIR/.env" << EOF
MYSQL_HOST=127.0.0.1
MYSQL_PORT=3307
MYSQL_USER=reddit_user
MYSQL_PASSWORD=reddit_password
MYSQL_DATABASE=reddit_comments
REDIS_HOST=127.0.0.1
REDIS_PORT=16379
REDIS_DB=0
JWT_SECRET_KEY=reddit-assistant-jwt-secret-key-$(date +%s)
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

    log "Configuration created at $INSTALL_DIR/.env"
}

launch_app() {
    log "Launching Reddit Comment Assistant..."

    source "$VENV_DIR/bin/activate"

    cd "$INSTALL_DIR"

    # Get the script directory
    SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

    # Copy app files if not present
    if [ ! -d "$INSTALL_DIR/app" ]; then
        log "Installing application files..."
        cp -r "$SCRIPT_DIR/app" "$INSTALL_DIR/"
        cp "$SCRIPT_DIR/requirements.txt" "$INSTALL_DIR/" 2>/dev/null || true
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

cleanup() {
    log "Cleaning up..."
    docker stop ${APP_NAME}-mysql ${APP_NAME}-redis 2>/dev/null || true
}

trap cleanup EXIT

main() {
    echo ""
    echo "=========================================="
    echo "  Reddit Comment Assistant"
    echo "  Installer & Launcher"
    echo "=========================================="
    echo ""

    detect_os
    check_python
    check_docker
    start_infrastructure
    setup_venv
    create_env_file
    launch_app
}

main "$@"
