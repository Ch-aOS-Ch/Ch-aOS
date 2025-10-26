#!/bin/bash
set -e
if [ ! "$LANGC" ]; then
  source scripts/ZA-Lang.sh
fi

set -a
source ./respostas.env
set +a

source ./lib/ui.sh
source ./lib/plugin.sh
source ./scripts/resources.sh

arquivo_plugin=$(select_or_create_plugin_file)
set_env_var "PLUGIN" "$arquivo_plugin"
export PLUGIN="$arquivo_plugin"

# --- Particionamento ---
if [ "$PARTITIONED" == "true" ]; then
  read -p "$MSG_PROMPT_RUN_AGAIN_PARTITION" -r choice
  if [[ "$choice" =~ ^[YySs]$ ]]; then
    bash scripts/A-particionamento.sh
  fi
else
  bash scripts/A-particionamento.sh
fi

# --- Reflector ---
if [ "$REFLECTORED" == "true" ]; then
  read -p "$MSG_PROMPT_RUN_AGAIN_REFLECTOR" -r choice
  if [[ "$choice" =~ ^[YySs]$ ]]; then
    bash scripts/B-reflector.sh
  fi
else
  bash scripts/B-reflector.sh
fi

# --- Instalação Base ---
if [ "$INSTALLED" == "true" ]; then
  read -p "$MSG_PROMPT_RUN_AGAIN_INSTALL" -r choice
  if [[ "$choice" =~ ^[YySs]$ ]]; then
    bash scripts/C-instalacao.sh
  fi
else
  bash scripts/C-instalacao.sh
fi
bash scripts/D-regiao.sh
bash scripts/E-personalizacao.sh
bash scripts/F-bootloader.sh

if [ "$FULLCODERAN" == "yes" ]; then
  PLAYBOOK_CHROOT_PATH="/mnt/root/Ch-aronte/main.yaml"
  PLAYBOOK_CH_OBOLOS_PATH="/mnt/root/Ch-aronte/Ch-obolos/$PLUGIN"
  cp -r ./ /mnt/root/Ch-aronte/
  arch-chroot /mnt ansible-playbook $PLAYBOOK_CHROOT_PATH --tags "$CHROOT_TAGS",region,users,bootloader,services -e @"$PLAYBOOK_CH_OBOLOS_PATH"
  if [ "$DOTS_ACCEPT" == "yes" ]; then
    echo "$MSG_LOADING_DOTS"
    arch-chroot /mnt ansible-playbook $PLAYBOOK_CHROOT_PATH --tags dotfiles -e @"$PLAYBOOK_CH_OBOLOS_PATH"
  fi
fi
