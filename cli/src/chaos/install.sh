#!/bin/bash
set -e

APP_DIR="/opt/chaos-app"
VENV_DIR="$APP_DIR/venv"
INSTALL_PATH="/usr/bin/chaos"
PYZ_PATH="$APP_DIR/chaos"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" &>/dev/null && pwd)"

function check_command() {
    if ! command -v "$1" &>/dev/null; then
        echo "Error: Command '$1' not found, but is required."
        exit 1
    fi
}

echo "Installing Ch-aOS Application..."

if [ "$(id -u)" -ne 0 ]; then
    echo "This script requires superuser (root) privileges."
    echo "Please run it with 'sudo' or as root."
    exit 1
fi

echo "Checking for required commands..."
check_command "python3"
PYTHON_EXEC=$(command -v python3)

echo "Warning: uv not found, using pip instead."

echo "(1/5) Creating APP dir, $APP_DIR"
mkdir -p "$APP_DIR"

echo "(2/5) Creating venv for chaos $VENV_DIR..."
"$PYTHON_EXEC" -m venv "$VENV_DIR" 2>/dev/null

cd "$SCRIPT_DIR"
if [ ! -f "requirements.txt" ]; then
    echo "Error: 'requirements.txt' not found in $SCRIPT_DIR."
    exit 1
fi

echo "(3/5) Installing deps..."
"$VENV_DIR/bin/pip" install -r "$SCRIPT_DIR/requirements.txt" 2>/dev/null

if [ ! -f "chaos" ]; then
    echo "error: 'chaos' not found in $SCRIPT_DIR."
    exit 1
fi

echo "(4/5) Installing chaos to $PYZ_PATH..."
mv chaos "$PYZ_PATH"

SHIV_CACHE_DIR="$APP_DIR/shiv_cache"
mkdir -p "$SHIV_CACHE_DIR"

echo "(5/5) Pre-warming shiv cache for zero trust boot..."
SHIV_ROOT="$SHIV_CACHE_DIR" "$VENV_DIR/bin/python" "$PYZ_PATH" --help >/dev/null

chmod -R 755 "$SHIV_CACHE_DIR"

tee "$INSTALL_PATH" >/dev/null <<EOF
#!/bin/bash

SHIV_ROOT="$SHIV_CACHE_DIR" exec "$VENV_DIR/bin/python" "$PYZ_PATH" "\$@"
EOF

chmod +x "$INSTALL_PATH"

echo ""
echo "Ch-aOS Application installed successfully!"
echo "Wrapper is in $INSTALL_PATH and the application is in $APP_DIR"
echo "Use the command 'chaos' to run the application."
