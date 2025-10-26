#!/bin/bash
set -e

# Carrega as bibliotecas e o ambiente
source ./lib/ui.sh
source ./lib/plugin.sh
source ./scripts/resources.sh
set -a
source ./respostas.env
set +a

# ==============================================================================
# FUNÇÃO HELPER PARA ESTE SCRIPT
# ==============================================================================

add_partition_to_plugin() {
  local part_name="$1"
  local part_size="$2"
  local part_type="$3"
  local part_num="$4"
  local part_mountpoint="$5"
  local part_important="$6"

  # Sempre type e name são strings. Part é número.
  local partition_yaml="{\"name\": \"$part_name\", \"size\": \"$part_size\", \"type\": \"$part_type\", \"part\": $part_num"

  if [[ -n "$part_mountpoint" && "$part_mountpoint" != "none" ]]; then
    partition_yaml="$partition_yaml, \"mountpoint\": \"$part_mountpoint\""
  fi
  if [[ -n "$part_important" ]]; then
    partition_yaml="$partition_yaml, \"important\": \"$part_important\""
  fi

  partition_yaml="$partition_yaml }"

  yq -iy ".particoes.partitions += [$partition_yaml]" "Ch-obolos/$PLUGIN"
}

# ==============================================================================
# FLUXO PRINCIPAL DO SCRIPT
# ==============================================================================

if [ "$LANGC" = "Portugues" ]; then loadkeys br-abnt2; else loadkeys us; fi
timedatectl

if [ -d /sys/firmware/efi ]; then
  plugin_set_value "firmware" "UEFI"
  set_env_var "FIRMWARE" "UEFI"
else
  plugin_set_value "firmware" "BIOS"
  set_env_var "FIRMWARE" "BIOS"
fi

confirmacao="n"
while ! [[ "$confirmacao" == "Y" || "$confirmacao" == "y" || "$confirmacao" == "" ]]; do
  echo "$MSG_LETS_PARTITION"
  sleep 1
  lsblk
  echo "---------------------------------------------------"

  read -p "$MSG_DISK_PROMPT" -r disco
  while [[ -z "$disco" || ! -b "/dev/$disco" ]]; do
    echo "$MSG_INVALID_DISK"
    read -p "$MSG_DISK_PROMPT" -r disco
  done
  plugin_set_value "particoes.disk" "/dev/$disco"
  yq -iy '.particoes.partitions = []' "Ch-obolos/$PLUGIN"

  # --- Partições Obrigatórias ---
  echo "--- Configurando partição BOOT (Obrigatória) ---"
  read -p "Número da partição para BOOT (ex: 1): " boot_part
  read -p "Tamanho da partição BOOT (ex: 1G): " boot_size
  read -p "Nome/Label para BOOT (ex: ESP): " boot_name
  add_partition_to_plugin "$boot_name" "$boot_size" "vfat" "$boot_part" "/boot" "boot"

  echo "--- Configurando partição ROOT (Obrigatória) ---"
  read -p "Número da partição para ROOT (ex: 2): " root_part
  read -p "Tamanho da partição ROOT (ex: 50G): " root_size
  read -p "Nome/Label para ROOT (ex: ARCH_ROOT): " root_name
  read -p "Formato para ROOT (ext4/btrfs): " root_type
  add_partition_to_plugin "$root_name" "$root_size" "$root_type" "$root_part" "/" "root"

  # --- Partições Opcionais ---
  read -rp "$MSG_WANT_HOME_PARTITION" want_home
  if [[ "$want_home" != "n" && "$want_home" != "N" ]]; then
    echo "--- Configurando partição HOME ---"
    read -p "Número da partição para HOME (ex: 3): " home_part
    read -p "Tamanho da partição HOME (ex: 100% para usar o resto): " home_size
    read -p "Nome/Label para HOME (ex: ARCH_HOME): " home_name
    add_partition_to_plugin "$home_name" "$home_size" "ext4" "$home_part" "/home" "home"
  fi

  read -rp "$MSG_WANT_SWAP_PARTITION" want_swap
  if [[ "$want_swap" != "n" && "$want_swap" != "N" ]]; then
    echo "--- Configurando partição SWAP ---"
    read -p "Número da partição para SWAP (ex: 4): " swap_part
    read -p "Tamanho da partição SWAP (ex: 8G): " swap_size
    read -p "Nome/Label para SWAP (ex: SWAP): " swap_name
    add_partition_to_plugin "$swap_name" "$swap_size" "linux-swap" "$swap_part" "none" "swap"
  fi

  # --- Loop de Verificação e Correção ---
  echo "---------------------------------------------------"
  echo "Configuração de partição gerada:"
  yq -o=json '.particoes' "Ch-obolos/$PLUGIN" | jq '.'
  echo "---------------------------------------------------"
  read -p "$MSG_CONFIRM_PROMPT" -r confirmacao

done

read -p "Qual bootloader você deseja usar? (grub/refind): " bootloader
plugin_set_value "bootloader" "$bootloader"

echo "$MSG_CONFIG_CONFIRMED"
echo "Executando Ansible para aplicar as mudanças..."
ansible-playbook -vvv ./main.yaml --tags particionamento -e @Ch-obolos/"$PLUGIN"

