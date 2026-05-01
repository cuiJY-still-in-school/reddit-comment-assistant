#!/usr/bin/env python3
"""
Reddit Comment Assistant - Interactive Setup Wizard
"""

import sys
import os
import subprocess
import shutil
import hashlib
import time
import socket

IS_WINDOWS = os.name == 'nt'
IS_MAC = sys.platform == 'darwin'
IS_LINUX = sys.platform.startswith('linux')

APP_NAME = "RedditCommentAssistant"
INSTALL_DIR = os.path.expanduser("~/.reddit-assistant")
VENV_DIR = os.path.join(INSTALL_DIR, "venv")


def print_banner():
    print()
    print("=" * 60)
    print("   Reddit Comment Assistant - Setup Wizard")
    print("=" * 60)
    print()


def cls():
    os.system('cls' if IS_WINDOWS else 'clear')


def step_header(current, total, title):
    print()
    print("─" * 60)
    print(f"  ⭐ Step {current}/{total}: {title}")
    print("─" * 60)


def success(msg):
    print(f"  ✅ {msg}")


def error(msg):
    print(f"  ❌ {msg}")


def info(msg):
    print(f"  ℹ️  {msg}")


def warn(msg):
    print(f"  ⚠️  {msg}")


def ask_yes_no(question, default=True):
    default_str = "[Y/n]" if default else "[y/N]"
    while True:
        answer = input(f"  {question} {default_str}: ").strip().lower()
        if not answer:
            return default
        if answer in ('y', 'yes'):
            return True
        if answer in ('n', 'no'):
            return False
        print("  Please enter y or n")


def ask_choice(question, options, default=0):
    print(f"\n  {question}")
    for i, opt in enumerate(options):
        marker = " ◀" if i == default else ""
        print(f"    {i+1}. {opt}{marker}")

    while True:
        try:
            choice = input(f"\n  Enter choice (1-{len(options)}): ").strip()
            if not choice:
                return options[default]
            idx = int(choice) - 1
            if 0 <= idx < len(options):
                return options[idx]
        except ValueError:
            pass
        print("  Invalid choice, try again")


def ask_input(question, default=""):
    result = input(f"  {question}" + (f" [{default}]" if default else "") + ": ").strip()
    return result or default


def ask_password(question):
    import getpass
    while True:
        p1 = getpass.getpass(f"  {question}: ")
        if not p1:
            return ""
        if len(p1) < 6:
            warn("Password must be at least 6 characters")
            continue
        p2 = getpass.getpass(f"  Confirm password: ")
        if p1 == p2:
            return p1
        error("Passwords don't match")


def check_docker():
    info("Checking Docker...")
    try:
        result = subprocess.run(["docker", "info"], capture_output=True, timeout=5)
        if result.returncode == 0:
            success("Docker is ready")
            return True
    except:
        pass
    warn("Docker not found or not running")
    return False


def start_docker_containers(mysql_port, redis_port):
    info("Starting MySQL container...")

    result = subprocess.run(
        ["docker", "ps", "-a", "--format", "{{.Names}}"],
        capture_output=True, text=True
    )
    containers = result.stdout.strip().split("\n") if result.stdout.strip() else []

    if f"{APP_NAME}-mysql" not in containers:
        subprocess.run([
            "docker", "run", "-d",
            "--name", f"{APP_NAME}-mysql",
            "-e", "MYSQL_ROOT_PASSWORD=root_password",
            "-e", "MYSQL_DATABASE=reddit_comments",
            "-e", "MYSQL_USER=reddit_user",
            "-e", "MYSQL_PASSWORD=reddit_password",
            "-p", f"{mysql_port}:3306",
            "mariadb:11.8",
            "--character-set-server=utf8mb4",
            "--collation-server=utf8mb4_unicode_ci"
        ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        success("MySQL container created")
    else:
        subprocess.run(["docker", "start", f"{APP_NAME}-mysql"],
                      stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        success("MySQL container started")

    info("Starting Redis container...")
    if f"{APP_NAME}-redis" not in containers:
        subprocess.run([
            "docker", "run", "-d",
            "--name", f"{APP_NAME}-redis",
            "-p", f"{redis_port}:6379",
            "redis:8.0-alpine"
        ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        success("Redis container created")
    else:
        subprocess.run(["docker", "start", f"{APP_NAME}-redis"],
                      stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        success("Redis container started")

    info("Waiting for MySQL to be ready...")
    for i in range(30):
        result = subprocess.run(
            ["docker", "exec", f"{APP_NAME}-mysql", "mysqladmin", "ping",
             "-h", "localhost", "-u", "root", "-proot_password"],
            capture_output=True
        )
        if result.returncode == 0:
            break
        time.sleep(1)
    success("MySQL is ready")

    info("Initializing database...")
    subprocess.run([
        "docker", "exec", f"{APP_NAME}-mysql", "mariadb",
        "-u", "root", "-proot_password", "-e",
        "CREATE DATABASE IF NOT EXISTS reddit_comments CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;"
        "CREATE USER IF NOT EXISTS 'reddit_user'@'%' IDENTIFIED BY 'reddit_password';"
        "GRANT ALL PRIVILEGES ON reddit_comments.* TO 'reddit_user'@'%';"
        "FLUSH PRIVILEGES;"
    ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    success("Database initialized")


def setup_venv():
    python_cmd = "python" if IS_WINDOWS else "python3"

    info("Creating virtual environment...")
    if not os.path.exists(VENV_DIR):
        subprocess.run([python_cmd, "-m", "venv", VENV_DIR], check=True)
    success("Virtual environment ready")

    if IS_WINDOWS:
        pip_path = os.path.join(VENV_DIR, "Scripts", "pip.exe")
        python_path = os.path.join(VENV_DIR, "Scripts", "python.exe")
    else:
        pip_path = os.path.join(VENV_DIR, "bin", "pip")
        python_path = os.path.join(VENV_DIR, "bin", "python")

    packages = [
        "fastapi", "uvicorn[standard]", "sqlalchemy[asyncio]",
        "aiomysql", "redis[hiredis]", "PyJWT", "bcrypt",
        "pydantic", "pydantic-settings", "python-dotenv",
        "httpx", "python-multipart", "alembic", "email-validator"
    ]

    info("Installing Python packages...")
    subprocess.run([pip_path, "install", "--upgrade", "pip"],
                  stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    for pkg in packages:
        subprocess.run([pip_path, "install", pkg],
                      stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    success("All packages installed")
    return python_path


def save_config(config, python_path):
    os.makedirs(INSTALL_DIR, exist_ok=True)

    jwt_secret = hashlib.sha256(str(time.time()).encode()).hexdigest()

    env_content = f"""# Reddit Comment Assistant - Configuration
# Generated by Setup Wizard

# Database
MYSQL_HOST=127.0.0.1
MYSQL_PORT={config['mysql_port']}
MYSQL_USER=reddit_user
MYSQL_PASSWORD=reddit_password
MYSQL_DATABASE=reddit_comments

# Redis
REDIS_HOST=127.0.0.1
REDIS_PORT={config['redis_port']}
REDIS_DB=0

# JWT
JWT_SECRET_KEY={jwt_secret}
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=1440

# DeepSeek (LLM)
DEEPSEEK_API_KEY={config.get('deepseek_key', '')}
DEEPSEEK_API_BASE=https://api.deepseek.com
DEEPSEEK_MODEL=deepseek-chat
DEEPSEEK_TIMEOUT=10

# Google OAuth
GOOGLE_CLIENT_ID={config.get('google_client_id', '')}
GOOGLE_CLIENT_SECRET={config.get('google_client_secret', '')}

# Rate Limiting
RATE_LIMIT_PER_MINUTE=10
LLM_CONCURRENT_LIMIT=5
CIRCUIT_BREAKER_THRESHOLD=5
CIRCUIT_BREAKER_RECOVERY_SECONDS=60

# App
APP_NAME=Reddit Comment Assistant
DEBUG=false
"""

    env_path = os.path.join(INSTALL_DIR, ".env")
    with open(env_path, "w") as f:
        f.write(env_content)
    success(f"Configuration saved")

    script_dir = os.path.dirname(os.path.abspath(__file__))
    src_app = os.path.join(script_dir, "..", "app")
    if os.path.exists(src_app) and not os.path.exists(os.path.join(INSTALL_DIR, "app")):
        shutil.copytree(src_app, os.path.join(INSTALL_DIR, "app"))
        success("Application files copied")

    src_req = os.path.join(script_dir, "..", "requirements.txt")
    if os.path.exists(src_req):
        shutil.copy(src_req, os.path.join(INSTALL_DIR, "requirements.txt"))

    return env_path


def launch(python_path):
    os.chdir(INSTALL_DIR)

    print()
    print("=" * 60)
    print("   🚀 Reddit Comment Assistant")
    print("=" * 60)
    print()
    print("  🌐  API Server:  http://localhost:8000")
    print("  📖  API Docs:   http://localhost:8000/docs")
    print()
    print("  💡 Open the URL above in your browser")
    print("  📝 Use the Chrome Extension to generate comments")
    print()
    print("  Press Ctrl+C to stop")
    print("=" * 60)
    print()

    subprocess.run([
        python_path, "-m", "uvicorn",
        "app.main:app",
        "--host", "0.0.0.0",
        "--port", "8000",
        "--reload"
    ])


def main():
    print_banner()

    if not check_docker():
        print()
        print("  Please install Docker first:")
        print("    Linux:     curl -fsSL https://get.docker.com | sh")
        print("    Mac:       https://docs.docker.com/desktop/install/mac-install/")
        print("    Windows:   https://docs.docker.com/desktop/install/windows-install/")
        input("\n  Press Enter to exit...")
        sys.exit(1)

    print()
    info("Let's configure your setup!")

    mysql_port = ask_input("MySQL port", "3307")
    redis_port = ask_input("Redis port", "16379")

    step_header(1, 4, "Database Setup")
    start_docker_containers(mysql_port, redis_port)

    step_header(2, 4, "Python Environment")
    python_path = setup_venv()

    step_header(3, 4, "API Keys (Optional)")

    print()
    info("DeepSeek API enables AI-powered comment generation")
    info("Without it, mock comments will be used")
    info("Get your key at: https://platform.deepseek.com/api_keys")
    print()
    use_deepseek = ask_yes_no("Do you have a DeepSeek API key?", default=False)

    deepseek_key = ""
    if use_deepseek:
        deepseek_key = ask_input("Enter your DeepSeek API key")

    print()
    info("Google OAuth enables social login (optional)")
    use_google = ask_yes_no("Do you want to configure Google OAuth?", default=False)

    google_client_id = ""
    google_client_secret = ""
    if use_google:
        google_client_id = ask_input("Google Client ID")
        google_client_secret = ask_input("Google Client Secret")

    step_header(4, 4, "Final Setup")
    config = {
        'mysql_port': mysql_port,
        'redis_port': redis_port,
        'deepseek_key': deepseek_key,
        'google_client_id': google_client_id,
        'google_client_secret': google_client_secret,
    }
    save_config(config, python_path)

    print()
    print("=" * 60)
    success("Setup Complete!")
    print("=" * 60)
    print()
    input("  Press Enter to launch the server...")

    try:
        launch(python_path)
    except KeyboardInterrupt:
        print("\n\n  Bye! 👋")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n  Setup cancelled")
        sys.exit(0)
    except Exception as e:
        error(f"Error: {e}")
        import traceback
        traceback.print_exc()
        input("\n  Press Enter to exit...")
        sys.exit(1)
