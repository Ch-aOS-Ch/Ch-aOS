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

echo "$MSG_START"
echo ""

# --- TIMEZONE ---
echo "$MSG_TIMEZONE_INFO"
read -p "$MSG_TIMEZONE_PROMPT" -r region

if [ -z "$region" ]; then
  region="$DEFAULT_REGION"
fi

# Validação robusta que verifica se o arquivo de fuso horário realmente existe.
while [ ! -f "/usr/share/zoneinfo/$region" ]; do
  echo "$MSG_INVALID_REGION"
  read -p "$MSG_TIMEZONE_PROMPT" -r region
  if [ -z "$region" ]; then
    region="$DEFAULT_REGION" # Garante que o default seja testado se o usuário digitar enter
  fi
done

# --- LOCALE & KEYMAP ---
echo ""
echo "$MSG_LOCALE_INFO"

# Coleta de múltiplos locales
declare -a locales=()
read -p "$MSG_LOCALE_PROMPT" -r main_locale
if [ -z "$main_locale" ]; then
  main_locale="$DEFAULT_LOCALE"
fi
locales+=("$main_locale")

add_another="s"
while [[ "$add_another" != "n" && "$add_another" != "N" ]]; do
  read -p "$MSG_ADD_ANOTHER_LOCALE" -r add_another
  if [[ "$add_another" == "n" || "$add_another" == "N" ]]; then
    break
  fi
  read -p "$MSG_NEXT_LOCALE_PROMPT" -r next_locale
  if [ -n "$next_locale" ]; then
    locales+=("$next_locale")
  fi
done

read -p "$MSG_KEYMAP_PROMPT" -r keymap
if [ -z "$keymap" ]; then
  keymap="$DEFAULT_KEYMAP"
fi

# --- DECLARAR (Salvar no Plugin) ---
plugin_set_value "region.timezone" "$region"
plugin_set_value "region.keymap" "$keymap"

# Cria a lista de locales no YAML
yq -iy '.region.locale = []' "Ch-obolos/$PLUGIN"
for loc in "${locales[@]}"; do
  plugin_add_to_list "region.locale" "${loc}.UTF-8"
done
echo "" >>Ch-obolos/$PLUGIN

echo ""
echo "$MSG_CONFIG_SAVED"

sleep 2
