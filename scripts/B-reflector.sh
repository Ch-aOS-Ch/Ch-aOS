#!/bin/bash
set -e
set -a
source respostas.env
set +a
source lib/ui.sh
case $LANGC in
"Portugues")
  REFLECTOR_COUNTRIES="-c br -c us"
  ;;
"English")
  REFLECTOR_COUNTRIES="-c eu -c us"
  ;;
esac

# ==============================================================================
# FLUXO PRINCIPAL DO SCRIPT
# ==============================================================================

sleep 1
echo "///...///"
sleep 1
echo "$MSG_ALMOST_FORGOT"
sleep 1
echo "$MSG_TYPING_SOUNDS"
sleep 1

# 1. Verifica se o reflector existe
if ! command -v reflector &>/dev/null; then
  echo "$MSG_INSTALLING"
  pacman -Syu --noconfirm reflector
fi

REFLECTOR_CMD="reflector $REFLECTOR_COUNTRIES --verbose --latest 25 --sort rate --save /etc/pacman.d/mirrorlist"
echo "$MSG_COMMAND_IS"
sleep 0.4
echo "$REFLECTOR_CMD"

$REFLECTOR_CMD
sleep 1

echo "$FINALIZESC"
