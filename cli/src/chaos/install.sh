#!/bin/bash
set -e

APP_DIR="/opt/chaos-app"
VENV_DIR="$APP_DIR/venv"
INSTALL_PATH="/usr/local/bin/chaos"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" &>/dev/null && pwd)"

function check_command() {
    if ! command -v "$1" &>/dev/null; then
        echo "Error: Command '$1' not found, but is required."
        exit 1
    fi
}

echo "Installing Ch-aOS Application (Native Architecture)..."

if [ "$(id -u)" -ne 0 ]; then
    echo "This script requires superuser (root) privileges."
    echo "Please run it with 'sudo' or as root."
    exit 1
fi

echo "Checking for required commands..."
check_command "python3"
PYTHON_EXEC=$(command -v python3)

echo "(1/4) Creating APP dir, $APP_DIR"
mkdir -p "$APP_DIR"

echo "(2/4) Creating venv for chaos $VENV_DIR..."
"$PYTHON_EXEC" -m venv "$VENV_DIR" 2>/dev/null

WHEEL_FILE=$(ls "$SCRIPT_DIR"/*.whl 2>/dev/null | head -n 1)

if [ -z "$WHEEL_FILE" ]; then
    echo "Error: No Ch-aOS .whl package found in $SCRIPT_DIR."
    exit 1
fi

echo "(3/4) Installing Ch-aOS and dependencies..."
"$VENV_DIR/bin/pip" install --quiet "$WHEEL_FILE"

echo "(4/4) Linking global executable..."
rm -f "$INSTALL_PATH"

ln -s "$VENV_DIR/bin/chaos" "$INSTALL_PATH"

echo ""
echo "Ch-aOS Application installed successfully!"
echo "Global command is linked at: $INSTALL_PATH"
echo "Core application lives in: $APP_DIR"
echo "Use the command 'chaos' to run."
