#!/bin/bash
set -e

function check_command() {
    if ! command -v "$1" &>/dev/null; then
        echo "Error: Command '$1' not found."
        if [ "$1" == "uv" ]; then
            echo "   Please install with: curl -LsSf https://astral.sh/uv/install.sh | sh"
        fi
        exit 1
    fi
}

CLI_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" &>/dev/null && pwd)"
VERSION="0.7.0"
DIST_DIR="$CLI_DIR/dist"
ARTIFACTS_DIR="$DIST_DIR/artifacts"
GPG_KEY=12FEDE6E939CA1DB84C222D55B8508C9C82A572E

echo "Checking for required tools..."
check_command "uv"
check_command "gpg"
echo "Found."

echo "Building v$VERSION (Native Wheel Architecture) ---"

echo "Cleansing previous builds..."
rm -rf "$DIST_DIR"
mkdir -p "$ARTIFACTS_DIR"

echo "Building the Python Wheel natively using uv..."
(
    cd "$CLI_DIR" || exit
    uv build --wheel
)

echo "Gathering artifacts..."
cp "$CLI_DIR/dist/"*.whl "$ARTIFACTS_DIR/"

echo "Placing install script..."
cp "$CLI_DIR/src/chaos/install.sh" "$ARTIFACTS_DIR/install.sh"
chmod +x "$ARTIFACTS_DIR/install.sh"

echo "Packaging distribution tarball..."
(
    cd "$ARTIFACTS_DIR" || exit
    tar -czvf "$DIST_DIR/chaos-v$VERSION.tar.gz" .
)

echo "Signing package with GPG key $GPG_KEY..."
gpg --detach-sign --armor -u "$GPG_KEY" "$DIST_DIR/chaos-v$VERSION.tar.gz"

echo "Cleaning up raw staging files..."
rm -rf "$ARTIFACTS_DIR"
rm -f "$DIST_DIR/"*.whl

echo ""
echo "Package build created at: $DIST_DIR/chaos-v$VERSION.tar.gz"
