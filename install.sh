#!/bin/bash
set -e

REPO_OWNER="Ch-aOS-Ch"
REPO_NAME="Ch-aOS"
VERSION="0.6.7"
ARTIFACT_FILENAME="chaos-v${VERSION}-shiv-dist.tar.gz"
SIG_FILE="${ARTIFACT_FILENAME}.asc"

GPG_KEY_URL="https://raw.githubusercontent.com/${REPO_OWNER}/${REPO_NAME}/main/chaos_pubkey.asc"

DOWNLOAD_URL="https://github.com/${REPO_OWNER}/${REPO_NAME}/releases/download/v${VERSION}/${ARTIFACT_FILENAME}"
SIGNATURE_URL="https://github.com/${REPO_OWNER}/${REPO_NAME}/releases/download/v${VERSION}/${SIG_FILE}"

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
check_command "gpg"

echo "Downloading and installing Ch-aOS v$VERSION and its sig..."
echo "Trying to download from: $DOWNLOAD_URL"

curl -Lsfo "$TEMP_DIR/$ARTIFACT_FILENAME" "$DOWNLOAD_URL"
curl -Lsfo "$TEMP_DIR/$SIG_FILE" "$SIG_FILE"

if [ ! -f "$TEMP_DIR/$ARTIFACT_FILENAME" ] || [ ! -f "$TEMP_DIR/$SIGNATURE_FILENAME" ]; then
  echo "Error: Failed to download the package or its signature. Exiting..."
  cleanup
  exit 1
fi
echo "Package and signature successfully downloaded."

gpg --quiet --import <(curl -sL "$GPG_KEY_URL")

echo "Verifying package integrity..."
if ! gpg --verify "$TEMP_DIR/$SIG_FILE" "$TEMP_DIR/$ARTIFACT_FILENAME" 2>/dev/null; then
  echo "GPG verification FAILED! The package is either corrupted or has been tampered with."
  echo "Aborting installation for security reasons."
  cleanup
  exit 1
fi
echo "GPG verification successful. The package is authentic."

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
