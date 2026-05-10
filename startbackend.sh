#!/bin/bash

# Reddit Comment Assistant - Backend Starter
# Usage: ./startbackend.sh

echo "=========================================="
echo "  Reddit Comment Assistant - Backend"
echo "=========================================="
echo ""

BACKEND_DIR="$(dirname "$0")/backend"

if [ ! -d "$BACKEND_DIR" ]; then
    echo "[ERROR] Backend directory not found: $BACKEND_DIR"
    exit 1
fi

cd "$BACKEND_DIR"

# Check if venv exists, create if not
if [ ! -d "venv" ]; then
    echo "[INFO] Creating Python virtual environment..."
    python3 -m venv venv
fi

# Activate venv
echo "[INFO] Activating virtual environment..."
source venv/bin/activate

# Check .env file
if [ ! -f ".env" ]; then
    echo "[WARN] .env file not found, creating default..."
    cat > .env << 'EOF'
MYSQL_HOST=127.0.0.1
MYSQL_PORT=3307
MYSQL_USER=reddit_user
MYSQL_PASSWORD=reddit_password
MYSQL_DATABASE=reddit_comments
REDIS_HOST=127.0.0.1
REDIS_PORT=16379
REDIS_DB=0
JWT_SECRET=reddit-assistant-dev-secret
JWT_EXPIRATION_MINUTES=1440
DEEPSEEK_API_KEY=
DEEPSEEK_BASE_URL=https://api.deepseek.com
DEEPSEEK_MODEL=deepseek-chat
APP_NAME=Reddit Comment Assistant
DEBUG=true
EOF
fi

# Check for DeepSeek API key
source .env 2>/dev/null
if [ -z "$DEEPSEEK_API_KEY" ] || [ "$DEEPSEEK_API_KEY" == "your-deepseek-api-key-here" ]; then
    echo ""
    echo "=========================================="
    echo "  DeepSeek API Key Required"
    echo "=========================================="
    echo "Please add your DeepSeek API key to backend/.env"
    echo "DEEPSEEK_API_KEY=your-key-here"
    echo ""
    echo "Get your API key at: https://platform.deepseek.com/"
    echo ""
fi

echo "[INFO] Starting backend server..."
echo "[INFO] Backend: http://localhost:8000"
echo "[INFO] API Docs: http://localhost:8000/docs"
echo "[INFO] Style Test: http://localhost:8000/style-test"
echo ""
echo "Press Ctrl+C to stop"
echo "=========================================="
echo ""

# Start uvicorn
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000