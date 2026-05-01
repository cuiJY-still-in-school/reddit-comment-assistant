#!/usr/bin/env python3
"""
Native Messaging Host for Reddit Comment Assistant
Allows Chrome extension to control Docker containers and API server
"""

import sys
import os
import json
import subprocess
import time
import socket
from threading import Thread

IS_WINDOWS = os.name == 'nt'
IS_MAC = sys.platform == 'darwin'
IS_LINUX = sys.platform.startswith('linux')

APP_NAME = "RedditCommentAssistant"
INSTALL_DIR = os.path.expanduser("~/.reddit-assistant")
VENV_DIR = os.path.join(INSTALL_DIR, "venv")


def log(msg):
    print(f"[NativeHost] {msg}", file=sys.stderr, flush=True)


def check_port(port):
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        sock.bind(('127.0.0.1', int(port)))
        sock.close()
        return True
    except OSError:
        return False


def docker_command(action, container=None, port=None):
    try:
        if action == 'start_mysql':
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
                    "-p", f"{port or 3307}:3306",
                    "mariadb:11.8",
                    "--character-set-server=utf8mb4",
                    "--collation-server=utf8mb4_unicode_ci"
                ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            else:
                subprocess.run(["docker", "start", f"{APP_NAME}-mysql"],
                            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            return {"success": True, "service": "mysql"}
        elif action == 'start_redis':
            result = subprocess.run(
                ["docker", "ps", "-a", "--format", "{{.Names}}"],
                capture_output=True, text=True
            )
            containers = result.stdout.strip().split("\n") if result.stdout.strip() else []
            if f"{APP_NAME}-redis" not in containers:
                subprocess.run([
                    "docker", "run", "-d",
                    "--name", f"{APP_NAME}-redis",
                    "-p", f"{port or 16379}:6379",
                    "redis:8.0-alpine"
                ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            else:
                subprocess.run(["docker", "start", f"{APP_NAME}-redis"],
                            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            return {"success": True, "service": "redis"}
        elif action == 'wait_mysql':
            for i in range(30):
                result = subprocess.run(
                    ["docker", "exec", f"{APP_NAME}-mysql", "mysqladmin", "ping",
                     "-h", "localhost", "-u", "root", "-proot_password"],
                    capture_output=True
                )
                if result.returncode == 0:
                    return {"success": True}
                time.sleep(1)
            return {"success": False, "error": "MySQL failed to start"}
        elif action == 'init_db':
            subprocess.run([
                "docker", "exec", f"{APP_NAME}-mysql", "mariadb",
                "-u", "root", "-proot_password", "-e",
                "CREATE DATABASE IF NOT EXISTS reddit_comments CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;"
                "CREATE USER IF NOT EXISTS 'reddit_user'@'%' IDENTIFIED BY 'reddit_password';"
                "GRANT ALL PRIVILEGES ON reddit_comments.* TO 'reddit_user'@'%';"
                "FLUSH PRIVILEGES;"
            ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            return {"success": True}
        elif action == 'start_api':
            if IS_WINDOWS:
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
            return {"success": True}
        elif action == 'check_api':
            try:
                import urllib.request
                response = urllib.request.urlopen('http://localhost:8000/health', timeout=2)
                return {"success": True, "running": True}
            except:
                return {"success": True, "running": False}
        return {"success": False, "error": "Unknown action"}
    except Exception as e:
        return {"success": False, "error": str(e)}


def handle_message(message):
    action = message.get('action', '')
    log(f"Received action: {action}")

    if action == 'start_all':
        # Start MySQL
        result = docker_command('start_mysql')
        if not result.get('success'):
            return json.dumps(result)

        # Start Redis
        result = docker_command('start_redis')
        if not result.get('success'):
            return json.dumps(result)

        # Wait for MySQL
        result = docker_command('wait_mysql')
        if not result.get('success'):
            return json.dumps(result)

        # Init DB
        result = docker_command('init_db')
        if not result.get('success'):
            return json.dumps(result)

        # Start API
        result = docker_command('start_api')
        return json.dumps({"success": True, "message": "All services started"})

    elif action == 'start_services':
        docker_command('start_mysql')
        docker_command('start_redis')
        docker_command('wait_mysql')
        docker_command('init_db')
        docker_command('start_api')
        return json.dumps({"success": True})

    elif action == 'check_status':
        result = docker_command('check_api')
        return json.dumps({
            "success": True,
            "api": result.get('running', False)
        })

    elif action == 'check':
        try:
            import urllib.request
            response = urllib.request.urlopen('http://localhost:8000/health', timeout=1)
            return json.dumps({"success": True, "api": True})
        except:
            return json.dumps({"success": True, "api": False})

    return json.dumps({"success": False, "error": "Unknown action"})


def read_message():
    # Read message length
    raw_length = sys.stdin.buffer.read(4)
    if not raw_length:
        return None
    length = int.from_bytes(raw_length, 'little')
    # Read message
    message = sys.stdin.buffer.read(length).decode('utf-8')
    return message


def send_message(message):
    encoded = message.encode('utf-8')
    sys.stdout.buffer.write(len(encoded).to_bytes(4, 'little'))
    sys.stdout.buffer.write(encoded)
    sys.stdout.buffer.flush()


def main():
    log("Native messaging host started")

    while True:
        try:
            message = read_message()
            if message is None:
                break

            log(f"Received: {message[:100]}...")
            response = handle_message(json.loads(message))
            send_message(response)
            log(f"Sent response: {response[:100]}...")

        except Exception as e:
            log(f"Error: {e}")
            break

    log("Native messaging host stopped")


if __name__ == '__main__':
    main()