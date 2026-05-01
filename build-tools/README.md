# Build Guide - Reddit Comment Assistant

## Overview

This directory contains build tools for creating distributable executables of Reddit Comment Assistant for all supported platforms.

## Supported Platforms

| Platform | Architecture | Output Format | Build Environment |
|----------|-------------|---------------|------------------|
| Windows | x86_64 | `.exe` (PyInstaller) | Windows with PyInstaller |
| Linux | x86_64 | `.sh` (Shell script) | Linux/macOS/Windows |
| Linux | ARM64 | `.sh` (Shell script) | Linux/macOS/Windows |
| macOS | Intel (x86_64) | `.sh` (Shell script) | macOS |
| macOS | M1/M2/M3/M4 (arm64) | `.sh` (Shell script) | macOS |

## Files

```
build-tools/
├── launcher.py          # Python launcher (used for PyInstaller)
├── launcher.spec        # PyInstaller spec for Windows .exe
├── install.sh           # Linux shell installer
├── install-mac.sh       # macOS shell installer
├── install.bat          # Windows batch installer
├── build.sh            # Build script (run on build machine)
└── dist/               # Output directory for built artifacts
    ├── RedditCommentAssistant.exe    # Windows x64 executable
    ├── reddit-assistant-linux-x86_64.sh
    ├── reddit-assistant-linux-arm64.sh
    ├── reddit-assistant-mac-intel.sh
    └── reddit-assistant-mac-arm64.sh
```

## Building

### Windows .exe (x64)

**Requirements:**
- Windows 10/11 x64
- Python 3.10+ installed
- PyInstaller: `pip install pyinstaller`

**Steps:**
```cmd
cd build-tools
pyinstaller launcher.spec --clean --noconfirm
```

The `.exe` will be created at `build-tools/dist/RedditCommentAssistant/`

**Note:** PyInstaller creates architecture-specific executables. To create a 32-bit Windows .exe, run PyInstaller on a 32-bit Windows system.

### Linux Shell Scripts

Shell scripts work on any Linux distribution with bash and Docker.

**Usage:**
```bash
chmod +x reddit-assistant-linux-x86_64.sh
./reddit-assistant-linux-x86_64.sh
```

### macOS Shell Scripts

**Usage:**
```bash
chmod +x reddit-assistant-mac-arm64.sh   # For M1/M2/M3/M4
# or
chmod +x reddit-assistant-mac-intel.sh   # For Intel Macs
./reddit-assistant-mac-arm64.sh
```

## What the Installer Does

1. **Detects OS and architecture**
2. **Checks/Installs Python** (if not present)
3. **Checks/Starts Docker** (for MySQL and Redis)
4. **Starts MySQL and Redis** via Docker containers
5. **Creates virtual environment** and installs dependencies
6. **Generates configuration** (`.env` file)
7. **Copies application files**
8. **Launches the API server** on port 8000

## Port Requirements

| Service | Port | Container Port |
|---------|------|----------------|
| MySQL | 3307 | 3306 |
| Redis | 16379 | 6379 |
| API Server | 8000 | - |

## First Run Setup

1. Run the installer for your platform
2. Wait for Docker images to download (first run only)
3. The API server starts automatically
4. Open http://localhost:8000/docs to access API documentation
5. Register a new account and start using the assistant

## Configuring DeepSeek LLM

After first run, edit `~/.reddit-assistant/.env` and add your DeepSeek API key:
```
DEEPSEEK_API_KEY=your_api_key_here
```

Then restart the application.

## Troubleshooting

### Docker not found
- Install Docker Desktop from https://docker.com
- On Linux: `curl -fsSL https://get.docker.com | sh`

### Python not found
- Download from https://python.org
- Ensure Python is in your PATH

### Ports already in use
- Stop other services using those ports, or
- Edit `~/.reddit-assistant/.env` to use different ports

### MySQL connection failed
- Ensure Docker is running
- Check if MySQL container started: `docker ps -a`

## File Locations

After installation:
- Config: `~/.reddit-assistant/.env`
- Virtual env: `~/.reddit-assistant/venv`
- App files: `~/.reddit-assistant/app`
- Docker containers: `RedditCommentAssistant-mysql`, `RedditCommentAssistant-redis`

## Uninstall

```bash
# Stop containers
docker stop RedditCommentAssistant-mysql RedditCommentAssistant-redis
docker rm RedditCommentAssistant-mysql RedditCommentAssistant-redis

# Remove installation directory
rm -rf ~/.reddit-assistant
```
