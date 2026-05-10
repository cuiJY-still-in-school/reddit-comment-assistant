#!/usr/bin/env python3
"""
Reddit Comment Assistant - Cross-Platform Launcher
Compiles to .exe using PyInstaller

Usage:
    python launcher.py                    # Development mode
    pyinstaller launcher.spec            # Build .exe
"""

import sys
import os
import subprocess
import time
import shutil
import hashlib

IS_WINDOWS = os.name == 'nt'
IS_MAC = sys.platform == 'darwin'
IS_LINUX = sys.platform.startswith('linux')

APP_NAME = "RedditCommentAssistant"
INSTALL_DIR = os.path.expanduser("~/.reddit-assistant")
VENV_DIR = os.path.join(INSTALL_DIR, "venv")

REQUIRED_PACKAGES = [
    "fastapi",
    "uvicorn[standard]",
    "sqlalchemy[asyncio]",
    "aiomysql",
    "redis[hiredis]",
    "PyJWT",
    "bcrypt",
    "pydantic",
    "pydantic-settings",
    "python-dotenv",
    "httpx",
    "python-multipart",
    "alembic",
    "email-validator",
]

MYSQL_PORT = "3307"
REDIS_PORT = "16379"
BACKEND_PORT = "8000"

def print_banner():
    print()
    print("=" * 50)
    print("  Reddit Comment Assistant")
    print("  Installer & Launcher")
    print("=" * 50)
    print()

def log_info(msg):
    print(f"[INFO] {msg}")

def log_warn(msg):
    print(f"[WARN] {msg}")

def log_error(msg):
    print(f"[ERROR] {msg}")

def run_command(cmd, check=True, capture=False, shell=False):
    """Run a shell command."""
    try:
        if isinstance(cmd, str) and not shell:
            cmd = cmd.split()
        result = subprocess.run(
            cmd,
            check=check,
            capture_output=capture,
            text=True,
            shell=shell
        )
        if capture:
            return result.stdout.strip(), result.returncode
        return None, result.returncode
    except subprocess.CalledProcessError as e:
        if check:
            log_error(f"Command failed: {e}")
            raise
        return None, e.returncode

def check_python():
    """Check if Python is installed."""
    log_info("Checking Python...")
    try:
        version = subprocess.run(
            ["python", "--version"],
            capture_output=True,
            text=True
        ).stdout.strip()
        log_info(f"Python: {version}")
        return True
    except FileNotFoundError:
        try:
            version = subprocess.run(
                ["python3", "--version"],
                capture_output=True,
                text=True
            ).stdout.strip()
            log_info(f"Python: {version}")
            return True
        except FileNotFoundError:
            log_error("Python not found. Please install Python 3.10+")
            return False

def check_docker():
    """Check and start Docker."""
    log_info("Checking Docker...")

    try:
        subprocess.run(["docker", "info"], capture_output=True, check=True)
        log_info("Docker is ready")
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        pass

    if IS_WINDOWS:
        log_warn("Docker not running. Starting Docker Desktop...")
        try:
            subprocess.Popen(
                ["C:\\Program Files\\Docker\\Docker\\Docker Desktop.exe"],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
            log_info("Waiting for Docker to start...")
            time.sleep(15)
            return True
        except FileNotFoundError:
            log_error("Docker not found. Please install Docker Desktop.")
            return False

    elif IS_MAC:
        log_warn("Docker not running. Please start Docker Desktop.")
        return False

    elif IS_LINUX:
        log_warn("Docker not running. Trying to start...")
        try:
            subprocess.run(["sudo", "systemctl", "start", "docker"], check=True)
            time.sleep(3)
            return True
        except:
            try:
                subprocess.run(["sudo", "service", "docker", "start"], check=True)
                time.sleep(3)
                return True
            except:
                log_error("Failed to start Docker. Try: sudo systemctl start docker")
                return False

    return False

def get_api_key():
    """Prompt user for DeepSeek API key."""
    print()
    print("=" * 50)
    print("  DeepSeek API Key")
    print("=" * 50)
    print()
    print("You need a DeepSeek API key for AI features.")
    print("Get one free at: https://platform.deepseek.com/")
    print()
    api_key = input("Enter your DeepSeek API key (or press Enter to skip): ").strip()
    return api_key

def start_infrastructure():
    """Start MySQL and Redis containers."""
    log_info("Starting MySQL and Redis containers...")

    result = subprocess.run(
        ["docker", "ps", "-a", "--format", "{{.Names}}"],
        capture_output=True,
        text=True
    )
    containers = result.stdout.strip().split("\n")

    if f"{APP_NAME}-mysql" not in containers:
        log_info("Creating MySQL container...")
        subprocess.run([
            "docker", "run", "-d",
            "--name", f"{APP_NAME}-mysql",
            "-e", "MYSQL_ROOT_PASSWORD=root_password",
            "-e", "MYSQL_DATABASE=reddit_comments",
            "-e", "MYSQL_USER=reddit_user",
            "-e", "MYSQL_PASSWORD=reddit_password",
            "-p", f"{MYSQL_PORT}:3306",
            "mariadb:11.8",
            "--character-set-server=utf8mb4",
            "--collation-server=utf8mb4_unicode_ci"
        ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    else:
        subprocess.run(["docker", "start", f"{APP_NAME}-mysql"],
                      stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    if f"{APP_NAME}-redis" not in containers:
        log_info("Creating Redis container...")
        subprocess.run([
            "docker", "run", "-d",
            "--name", f"{APP_NAME}-redis",
            "-p", f"{REDIS_PORT}:6379",
            "redis:8.0-alpine"
        ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    else:
        subprocess.run(["docker", "start", f"{APP_NAME}-redis"],
                      stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    log_info("Waiting for MySQL...")
    for _ in range(30):
        result = subprocess.run(
            ["docker", "exec", f"{APP_NAME}-mysql", "mysqladmin", "ping",
             "-h", "localhost", "-u", "root", "-proot_password"],
            capture_output=True
        )
        if result.returncode == 0:
            break
        time.sleep(1)

    log_info("Initializing database...")
    subprocess.run([
        "docker", "exec", f"{APP_NAME}-mysql", "mariadb",
        "-u", "root", "-proot_password", "-e",
        "CREATE DATABASE IF NOT EXISTS reddit_comments CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;"
    ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    subprocess.run([
        "docker", "exec", f"{APP_NAME}-mysql", "mariadb",
        "-u", "root", "-proot_password", "-e",
        "CREATE USER IF NOT EXISTS 'reddit_user'@'%' IDENTIFIED BY 'reddit_password';"
        "GRANT ALL PRIVILEGES ON reddit_comments.* TO 'reddit_user'@'%';"
        "FLUSH PRIVILEGES;"
    ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    log_info("Infrastructure ready")

def create_virtualenv():
    """Create and populate virtual environment."""
    log_info("Setting up virtual environment...")

    python_cmd = "python" if IS_WINDOWS else "python3"

    if not os.path.exists(VENV_DIR):
        subprocess.run([python_cmd, "-m", "venv", VENV_DIR], check=True)

    if IS_WINDOWS:
        pip_path = os.path.join(VENV_DIR, "Scripts", "pip.exe")
        python_path = os.path.join(VENV_DIR, "Scripts", "python.exe")
    else:
        pip_path = os.path.join(VENV_DIR, "bin", "pip")
        python_path = os.path.join(VENV_DIR, "bin", "python")

    log_info("Installing dependencies (this may take a while)...")
    subprocess.run([pip_path, "install", "--upgrade", "pip"],
                   stdout=subprocess.DEVNULL)

    for pkg in REQUIRED_PACKAGES:
        log_info(f"  Installing {pkg}...")
        subprocess.run([pip_path, "install", pkg],
                      stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    log_info("Dependencies installed")

def create_config(api_key):
    """Create .env configuration file."""
    log_info("Creating configuration...")

    os.makedirs(INSTALL_DIR, exist_ok=True)

    jwt_secret = hashlib.sha256(str(time.time()).encode()).hexdigest()

    env_content = f"""# Database
MYSQL_HOST=127.0.0.1
MYSQL_PORT={MYSQL_PORT}
MYSQL_USER=reddit_user
MYSQL_PASSWORD=reddit_password
MYSQL_DATABASE=reddit_comments

# Redis
REDIS_HOST=127.0.0.1
REDIS_PORT={REDIS_PORT}
REDIS_DB=0

# JWT
JWT_SECRET={jwt_secret}
JWT_EXPIRATION_MINUTES=1440

# DeepSeek (LLM)
DEEPSEEK_API_KEY={api_key}
DEEPSEEK_BASE_URL=https://api.deepseek.com
DEEPSEEK_MODEL=deepseek-chat

# App
APP_NAME=Reddit Comment Assistant
DEBUG=false
"""

    env_path = os.path.join(INSTALL_DIR, ".env")
    with open(env_path, "w") as f:
        f.write(env_content)

    log_info(f"Configuration saved to {env_path}")

def get_app_dir():
    """Get the directory containing the app files."""
    if getattr(sys, 'frozen', False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.abspath(__file__))

def copy_app_files():
    """Copy app files to installation directory."""
    app_dir = get_app_dir()

    target_backend_dir = os.path.join(INSTALL_DIR, "backend")

    if os.path.exists(os.path.join(app_dir, "backend")):
        log_info("Copying application files...")
        if os.path.exists(target_backend_dir):
            shutil.rmtree(target_backend_dir)
        shutil.copytree(os.path.join(app_dir, "backend"), target_backend_dir)

def launch_server():
    """Launch the FastAPI server."""
    log_info("Launching Reddit Comment Assistant...")

    if IS_WINDOWS:
        python_path = os.path.join(VENV_DIR, "Scripts", "python.exe")
    else:
        python_path = os.path.join(VENV_DIR, "bin", "python")

    os.chdir(INSTALL_DIR)

    print()
    print("=" * 50)
    print("  Reddit Comment Assistant")
    print("=" * 50)
    print()
    print("  API Server: http://localhost:" + BACKEND_PORT)
    print("  API Docs:   http://localhost:" + BACKEND_PORT + "/docs")
    print()
    print("  Press Ctrl+C to stop")
    print("=" * 50)
    print()

    subprocess.run([
        python_path, "-m", "uvicorn",
        "app.main:app",
        "--host", "0.0.0.0",
        "--port", BACKEND_PORT
    ])

def main():
    print_banner()

    if not check_python():
        input("Press Enter to exit...")
        sys.exit(1)

    if not check_docker():
        input("Press Enter to exit...")
        sys.exit(1)

    api_key = get_api_key()
    start_infrastructure()
    create_virtualenv()
    create_config(api_key)
    copy_app_files()
    launch_server()

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n[INFO] Shutting down...")
        if IS_WINDOWS:
            subprocess.run(["docker", "stop", f"{APP_NAME}-mysql", f"{APP_NAME}-redis"],
                          stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        print("[INFO] Goodbye!")
    except Exception as e:
        log_error(f"Unexpected error: {e}")
        input("Press Enter to exit...")
        sys.exit(1)