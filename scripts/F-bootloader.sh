#!/bin/bash
set -e

source ./lib/ui.sh
source ./lib/plugin.sh
source ./scripts/resources.sh
set -a
source ./respostas.env
set +a

# ==============================================================================
# FLUXO PRINCIPAL DO SCRIPT
# ==============================================================================
echo "$MSG_START_BOOTLOADER"
sleep 1

# Garante que o NetworkManager está no plugin antes de executar as roles
echo "$MSG_ENABLE_NETWORK"
yq -iy '.services |= (select(.) // []) | . + [{"name": "NetworkManager", "state": "started", "enabled": true}] | unique_by(.name)' "Ch-obolos/$PLUGIN"

echo "$MSG_CONFIGURING"

echo "---------------------------------------------------"
echo "$MSG_GOODBYE_1"
echo "$MSG_GOODBYE_2"
echo "$MSG_GOODBYE_3"
export FULLCODERAN="yes"
