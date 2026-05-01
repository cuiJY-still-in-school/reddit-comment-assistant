import subprocess
import time
import os
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse, HTMLResponse
from contextlib import asynccontextmanager
from app.config import settings
from app.database import init_db
from app.utils.cache import init_redis, close_redis
from app.utils.rate_limiter import init_rate_limiter
from app.api.auth import router as auth_router
from app.api.persona import router as persona_router
from app.api.comment import router as comment_router


APP_NAME = "RedditCommentAssistant"
INSTALL_DIR = os.path.expanduser("~/.reddit-assistant")
VENV_DIR = os.path.join(INSTALL_DIR, "venv")


def docker_command(cmd_list):
    try:
        result = subprocess.run(cmd_list, capture_output=True, text=True, timeout=30)
        return result.returncode == 0, result.stdout, result.stderr
    except Exception as e:
        return False, "", str(e)


def start_docker_mysql():
    # Check if container exists
    result = subprocess.run(
        ["docker", "ps", "-a", "--format", "{{.Names}}"],
        capture_output=True, text=True
    )
    containers = result.stdout.strip().split("\n") if result.stdout.strip() else []

    if f"{APP_NAME}-mysql" not in containers:
        subprocess.Popen([
            "docker", "run", "-d",
            "--name", f"{APP_NAME}-mysql",
            "-e", "MYSQL_ROOT_PASSWORD=root_password",
            "-e", "MYSQL_DATABASE=reddit_comments",
            "-e", "MYSQL_USER=reddit_user",
            "-e", "MYSQL_PASSWORD=reddit_password",
            "-p", "3307:3306",
            "mariadb:11.8",
            "--character-set-server=utf8mb4",
            "--collation-server=utf8mb4_unicode_ci"
        ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    else:
        subprocess.Popen(["docker", "start", f"{APP_NAME}-mysql"],
                        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    return True


def start_docker_redis():
    result = subprocess.run(
        ["docker", "ps", "-a", "--format", "{{.Names}}"],
        capture_output=True, text=True
    )
    containers = result.stdout.strip().split("\n") if result.stdout.strip() else []

    if f"{APP_NAME}-redis" not in containers:
        subprocess.Popen([
            "docker", "run", "-d",
            "--name", f"{APP_NAME}-redis",
            "-p", "16379:6379",
            "redis:8.0-alpine"
        ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    else:
        subprocess.Popen(["docker", "start", f"{APP_NAME}-redis"],
                        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    return True


def wait_for_mysql():
    for i in range(30):
        result = subprocess.run(
            ["docker", "exec", f"{APP_NAME}-mysql", "mysqladmin", "ping",
             "-h", "localhost", "-u", "root", "-proot_password"],
            capture_output=True
        )
        if result.returncode == 0:
            return True
        time.sleep(1)
    return False


def init_database():
    subprocess.run([
        "docker", "exec", f"{APP_NAME}-mysql", "mariadb",
        "-u", "root", "-proot_password", "-e",
        "CREATE DATABASE IF NOT EXISTS reddit_comments CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;"
        "CREATE USER IF NOT EXISTS 'reddit_user'@'%' IDENTIFIED BY 'reddit_password';"
        "GRANT ALL PRIVILEGES ON reddit_comments.* TO 'reddit_user'@'%';"
        "FLUSH PRIVILEGES;"
    ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


def start_api_server():
    import sys
    if os.name == 'nt':
        python_path = os.path.join(VENV_DIR, "Scripts", "python.exe")
    else:
        python_path = os.path.join(VENV_DIR, "bin", "python")

    os.chdir(INSTALL_DIR)
    subprocess.Popen([
        python_path, "-m", "uvicorn",
        "app.main:app",
        "--host", "0.0.0.0",
        "--port", "8000"
    ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    await init_redis()
    await init_rate_limiter()
    yield
    await close_redis()


app = FastAPI(
    title=settings.app_name,
    version="1.0.0",
    lifespan=lifespan,
)

app.include_router(auth_router)
app.include_router(persona_router)
app.include_router(comment_router)


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content={"success": False, "message": exc.detail},
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=500,
        content={"success": False, "message": "系统繁忙，请稍后重试", "detail": str(exc) if settings.debug else None},
    )


@app.get("/")
async def root():
    return {"message": "Reddit Comment Assistant API", "version": "1.0.0"}


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.get("/launcher")
async def launcher():
    html_path = os.path.join(os.path.dirname(__file__), "..", "launcher-page", "index.html")
    with open(html_path, "r") as f:
        return HTMLResponse(content=f.read())


@app.post("/launch/start_mysql")
async def start_mysql():
    try:
        start_docker_mysql()
        return {"success": True, "message": "MySQL container starting"}
    except Exception as e:
        return {"success": False, "error": str(e)}


@app.post("/launch/start_redis")
async def start_redis():
    try:
        start_docker_redis()
        return {"success": True, "message": "Redis container starting"}
    except Exception as e:
        return {"success": False, "error": str(e)}


@app.post("/launch/wait_mysql")
async def wait_mysql():
    try:
        success = wait_for_mysql()
        return {"success": success, "message": "MySQL ready" if success else "MySQL not ready"}
    except Exception as e:
        return {"success": False, "error": str(e)}


@app.post("/launch/init_db")
async def init_db_endpoint():
    try:
        init_database()
        return {"success": True, "message": "Database initialized"}
    except Exception as e:
        return {"success": False, "error": str(e)}


@app.post("/launch/start_api")
async def start_api():
    try:
        start_api_server()
        return {"success": True, "message": "API server starting"}
    except Exception as e:
        return {"success": False, "error": str(e)}


@app.post("/launch/start_all")
async def start_all():
    try:
        start_docker_mysql()
        start_docker_redis()
        wait_for_mysql()
        init_database()
        start_api_server()
        return {"success": True, "message": "All services starting"}
    except Exception as e:
        return {"success": False, "error": str(e)}


@app.get("/launch/status")
async def launch_status():
    api_ok = False
    try:
        import urllib.request
        urllib.request.urlopen('http://localhost:8000/health', timeout=1)
        api_ok = True
    except:
        pass

    return {
        "success": True,
        "api": api_ok,
        "mysql": api_ok,
        "redis": api_ok
    }