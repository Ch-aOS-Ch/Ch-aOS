#!/bin/bash
set -e

function check_command() {
  if ! command -v "$1" &>/dev/null; then
    echo "Error: Command '$1' not found."
    if [ "$1" == "uv" ]; then
      echo "   Please install with: curl -LsSf https://astral.sh/uv/install.sh | sh"
    elif [ "$1" == "shiv" ]; then
      echo "   Please install with: uv pip install shiv  (ou pip install shiv)"
    fi
    exit 1
  fi
}

CLI_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" &>/dev/null && pwd)"
VERSION="0.6.2"
DIST_DIR="$CLI_DIR/dist"
ARTIFACTS_DIR="$DIST_DIR/artifacts"

echo "Checking for uv and shiv..."
check_command "uv"
check_command "shiv"
echo "Found."

echo "building v$VERSION ---"

echo "Cleansing previous builds..."
rm -rf "$DIST_DIR"
mkdir -p "$ARTIFACTS_DIR"

echo "Creating new requirements.txt..."
uv pip compile "$CLI_DIR/pyproject.toml" -o "$ARTIFACTS_DIR/requirements.txt"

echo "Building the with shiv --no-deps..."
(
  cd "$CLI_DIR" || exit
  shiv . -c chaos --no-deps -o "$ARTIFACTS_DIR/chaos"
)

echo "Placing install script..."
cp "$CLI_DIR/src/chaos/install.sh" "$ARTIFACTS_DIR/install.sh"
chmod +x "$ARTIFACTS_DIR/install.sh"

echo "Packaging..."
(
  cd "$ARTIFACTS_DIR" || exit
  tar -czvf "$DIST_DIR/chaos-v$VERSION-shiv-dist.tar.gz" .
)

rm -rf "$ARTIFACTS_DIR"
echo ""
echo "Package build created at: $DIST_DIR/chaos-v$VERSION-shiv-dist.tar.gz"
