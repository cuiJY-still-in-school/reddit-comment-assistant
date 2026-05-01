#!/bin/bash
# ============================================
# Build Script for Reddit Comment Assistant
# Creates executables for Windows, Mac, Linux
# ============================================

set -e

BUILD_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$BUILD_DIR/.." && pwd)"
BUILD_OUTPUT="$BUILD_DIR/dist"

mkdir -p "$BUILD_OUTPUT"

echo "============================================"
echo "  Reddit Comment Assistant - Build Script"
echo "============================================"
echo ""

build_windows() {
    echo "[INFO] Building Windows x64 executable..."
    echo "[INFO] Note: Run this on Windows with PyInstaller installed"

    if [ ! -f "/c/Windows/System32/pyinstaller.exe" ] && ! command -v pyinstaller &> /dev/null; then
        echo "[WARN] PyInstaller not found. Install with: pip install pyinstaller"
        echo "[INFO] Then run: pyinstaller launcher.spec"
        return 1
    fi

    cd "$BUILD_DIR"

    if command -v pyinstaller &> /dev/null; then
        pyinstaller launcher.spec --clean --noconfirm
        echo "[INFO] Windows .exe built at: $BUILD_DIR/dist/RedditCommentAssistant/"
    else
        echo "[INFO] Windows build requires running on Windows"
    fi
}

build_linux_shell() {
    echo "[INFO] Creating Linux shell installer..."

    local output="$BUILD_OUTPUT/reddit-assistant-linux-x86_64.sh"
    cp "$BUILD_DIR/install.sh" "$output"
    chmod +x "$output"
    echo "[INFO] Linux shell installer: $output"
}

build_linux_arm64_shell() {
    echo "[INFO] Creating Linux ARM64 shell installer..."

    local output="$BUILD_OUTPUT/reddit-assistant-linux-arm64.sh"
    cp "$BUILD_DIR/install.sh" "$output"
    chmod +x "$output"
    echo "[INFO] Linux ARM64 shell installer: $output"
}

build_mac_intel_shell() {
    echo "[INFO] Creating Mac Intel shell installer..."

    local output="$BUILD_OUTPUT/reddit-assistant-mac-intel.sh"
    cp "$BUILD_DIR/install.sh" "$output"
    chmod +x "$output"
    echo "[INFO] Mac Intel shell installer: $output"
}

build_mac_arm64_shell() {
    echo "[INFO] Creating Mac M1/M2/M3/M4 shell installer..."

    local output="$BUILD_OUTPUT/reddit-assistant-mac-arm64.sh"
    cp "$BUILD_DIR/install.sh" "$output"
    chmod +x "$output"
    echo "[INFO] Mac ARM64 shell installer: $output"
}

echo "[INFO] Select platform to build:"
echo "  1. Windows x64 (.exe)"
echo "  2. Linux x86_64 (.sh)"
echo "  3. Linux ARM64 (.sh)"
echo "  4. Mac Intel (.sh)"
echo "  5. Mac M1/M2/M3/M4 (.sh)"
echo "  6. All (except Windows .exe)"
echo ""

read -p "Enter choice (1-6): " choice

case $choice in
    1) build_windows ;;
    2) build_linux_shell ;;
    3) build_linux_arm64_shell ;;
    4) build_mac_intel_shell ;;
    5) build_mac_arm64_shell ;;
    6)
        build_linux_shell
        build_linux_arm64_shell
        build_mac_intel_shell
        build_mac_arm64_shell
        ;;
    *) echo "[ERROR] Invalid choice" ;;
esac

echo ""
echo "[INFO] Build artifacts in: $BUILD_OUTPUT"
echo "[INFO] Done!"
