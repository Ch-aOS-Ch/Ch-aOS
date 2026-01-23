#!/bin/bash
set -e

REPO_OWNER="Ch-aOS-Ch"
REPO_NAME="Ch-aOS"
VERSION="0.6.2"
ARTIFACT_FILENAME="chaos-v${VERSION}-shiv-dist.tar.gz"

DOWNLOAD_URL="https://github.com/${REPO_OWNER}/${REPO_NAME}/releases/download/v${VERSION}/${ARTIFACT_FILENAME}"

TEMP_DIR=$(mktemp -d)
INSTALLER_SCRIPT="install.sh"

function check_command() {
  if ! command -v "$1" &>/dev/null; then
    echo "Error: Command '$1' not found, but is required."
    exit 1
  fi
}

function cleanup() {
  echo "Cleansing temporary files..."
  rm -rf "$TEMP_DIR"
}

if [ "$(id -u)" -ne 0 ]; then
  echo "This script requires superuser (root) privileges."
  echo "Please run it with 'sudo' or as root."
  exit 1
fi

echo "checking for required commands..."
check_command "curl"
check_command "tar"

echo "Downloading and installing Ch-aOS v$VERSION..."
echo "Trying to download from: $DOWNLOAD_URL"

curl -Lsfo "$TEMP_DIR/$ARTIFACT_FILENAME" "$DOWNLOAD_URL"
if [ ! -f "$TEMP_DIR/$ARTIFACT_FILENAME" ]; then
  echo "Error: Failed to download the package. Exiting..."
  cleanup
  exit 1
fi

echo "Package successfully downloaded to $TEMP_DIR/$ARTIFACT_FILENAME"

echo "Untarring the package..."
tar -xzvf "$TEMP_DIR/$ARTIFACT_FILENAME" -C "$TEMP_DIR"
echo "Package successfully extracted to $TEMP_DIR"

echo "Executing the installer script..."
INSTALLER_IN_TEMP="$TEMP_DIR/$INSTALLER_SCRIPT"

if [ ! -f "$INSTALLER_IN_TEMP" ]; then
  echo "Error: Installer script not found in the extracted package. Exiting..."
  cleanup
  exit 1
fi

chmod +x "$INSTALLER_IN_TEMP"
"$INSTALLER_IN_TEMP"

echo "Installation script executed successfully."
echo "Cleaning up"
trap - EXIT
cleanup

echo ""
echo "Success."
echo "Use 'chaos' and 'chaos explain -h' to get started."

echo "If you wish to enable command autocompletion for the 'chaos' CLI tool, follow the instructions below:"
if [ -n "$SUDO_USER" ]; then
  USER_SHELL=$(getent passwd "$SUDO_USER" | cut -d: -f7)
else
  USER_SHELL="$SHELL"
fi

echo "To activate autocompletion, add the following to your shell's initialization file:"
echo ""

if [[ "$USER_SHELL" == *"/bash"* ]]; then
  echo -e "\033[1mFor bash:\033[0m"
  echo "  echo 'eval \"\$(chaos -t)\"' >> ~/.bashrc"
  echo "Then restart your shell or run: source ~/.bashrc"
elif [[ "$USER_SHELL" == *"/zsh"* ]]; then
  echo -e "\033[1mFor Zsh:\033[0m"
  echo "  echo 'eval \"\$(chaos -t)\"' >> ~/.zshrc"
  echo "Then restart your shell or run: source ~/.zshrc"
elif [[ "$USER_SHELL" == *"/fish"* ]]; then
  echo -e "\033[1mFor Fish:\033[0m"
  echo "  register-python-argcomplete --shell fish chaos > ~/.config/fish/completions/chaos.fish"
  echo "  Then restart your shell"
else
  echo "Your shell ($USER_SHELL) Could not be automatically fetched."
  echo "To enable autocompletion, run the following command in your shell:"
  echo "  eval \"\$(register-python-argcomplete chaos)\""
fi
echo ""
