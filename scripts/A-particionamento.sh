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
# FLUXO PRINCIPAL DO SCRIPT
# ==============================================================================

if [ "$LANGC" = "Portugues" ]; then loadkeys br-abnt2; else loadkeys us; fi
timedatectl

arquivo_plugin=$(select_or_create_plugin_file)
set_env_var "PLUGIN" "$arquivo_plugin"
export PLUGIN="$arquivo_plugin"

if [ -d /sys/firmware/efi ]; then
  plugin_set_value "firmware" "UEFI"
  set_env_var "FIRMWARE" "UEFI"
  firmware="UEFI"
else
  plugin_set_value "firmware" "BIOS"
  set_env_var "FIRMWARE" "BIOS"
  firmware="BIOS"
fi

echo "$MSG_PREPARING"
sleep 1
echo "3..."
sleep 1
echo "2..."
sleep 1
echo "1..."
echo "$MSG_STARTING_PROMPT"
echo ""
echo "$MSG_LETS_PARTITION"
echo "$MSG_CFDISK_INFO"
echo ""
echo "$MSG_RECOMMENDATION"
echo "$MSG_RECOMMENDATION_DETAILS"
echo "$MSG_FINALIZE"
echo "---------------------------------------------------"

read -p "$MSG_UNDERSTOOD_PROMPT" -r resposta
while [[ "$resposta" == "Y" || "$resposta" == "y" || "$resposta" == "" ]]; do
  echo "$MSG_READ_AGAIN"
  read -p "$MSG_UNDERSTOOD_PROMPT" -r resposta
done

echo "$MSG_CONTINUING"
sleep 1
echo "---------------------------------------------------"
lsblk
echo "---------------------------------------------------"

read -p "$MSG_DISK_PROMPT" -r disco
while [[ -z "$disco" || ! -b "/dev/$disco" ]]; do
  echo "$MSG_INVALID_DISK"
  read -p "$MSG_DISK_PROMPT" -r disco
done

cfdisk "/dev/$disco"

# Coleta das informações de partição
root_dev=$(prompt_for_partition "$MSG_ROOT_PROMPT")
root_label=$(prompt_for_label "$MSG_ROOT_LABEL_PROMPT")
boot_dev=$(prompt_for_partition "$MSG_BOOT_PROMPT")
boot_label=$(prompt_for_label "$MSG_BOOT_LABEL_PROMPT")

read -rp "$MSG_WANT_HOME_PARTITION" want_home
if [[ "$want_home" == "Y" || "$want_home" == "y" || "$want_home" == "" ]]; then
  home_dev=$(prompt_for_partition "$MSG_HOME_PROMPT")
  home_label=$(prompt_for_label "$MSG_HOME_LABEL_PROMPT")
else
  home_dev=""
  home_label=""
fi

read -rp "$MSG_WANT_SWAP_PARTITION" want_swap
if [[ "$want_swap" == "Y" || "$want_swap" == "y" || "$want_swap" == "" ]]; then
  swap_dev=$(prompt_for_partition "$MSG_SWAP_PROMPT")
  swap_label=$(prompt_for_label "$MSG_SWAP_LABEL_PROMPT")
else
  swap_dev=""
  swap_label=""
fi

read -p "$MSG_FORMAT_PROMPT" -r formato
while [[ "$formato" != "btrfs" && "$formato" != "ext4" ]]; do
  echo "$MSG_INVALID_FORMAT"
  read -p "$MSG_FORMAT_PROMPT" -r formato
done

bootloader=$(prompt_for_bootloader)

# Loop de verificação e correção
confirmacao="n"
while ! [[ "$confirmacao" == "Y" || "$confirmacao" == "y" || "$confirmacao" == "" ]]; do
  echo ""
  echo "---------------------------------------------------"
  echo "$MSG_CHECK_VALUES"
  echo "  [DISCO]      => /dev/$disco"
  echo "  [ROOT]       => Device: /dev/$root_dev, Label: $root_label"
  echo "  [HOME]       => Device: /dev/$home_dev, Label: $home_label"
  echo "  [BOOT]       => Device: /dev/$boot_dev, Label: $boot_label"
  echo "  [SWAP]       => Device: /dev/$swap_dev, Label: $swap_label"
  echo "  [FORMATO]    => $formato"
  echo "  [FIRMWARE]   => $firmware"
  echo "  [BOOTLOADER] => $bootloader"
  echo "---------------------------------------------------"

  read -p "$MSG_CONFIRM_PROMPT" -r confirmacao

  if ! [[ "$confirmacao" == "Y" || "$confirmacao" == "y" || "$confirmacao" == "" ]]; then
    read -p "$MSG_CHANGE_PROMPT" -r var_to_change
    case $(echo "$var_to_change" | tr '[:upper:]' '[:lower:]') in
    root)
      root_dev=$(prompt_for_partition "$MSG_ROOT_PROMPT")
      root_label=$(prompt_for_label "$MSG_ROOT_LABEL_PROMPT")
      ;;
    home)
      home_dev=$(prompt_for_partition "$MSG_HOME_PROMPT")
      home_label=$(prompt_for_label "$MSG_HOME_LABEL_PROMPT")
      ;;
    boot)
      boot_dev=$(prompt_for_partition "$MSG_BOOT_PROMPT")
      boot_label=$(prompt_for_label "$MSG_BOOT_LABEL_PROMPT")
      ;;
    swap)
      swap_dev=$(prompt_for_partition "$MSG_SWAP_PROMPT")
      swap_label=$(prompt_for_label "$MSG_SWAP_LABEL_PROMPT")
      ;;
    disco)
      read -p "$MSG_DISK_PROMPT" -r disco
      while [[ -z "$disco" || ! -b "/dev/$disco" ]]; do
        echo "$MSG_INVALID_DISK"
        read -p "$MSG_DISK_PROMPT" -r disco
      done
      ;;
    formato)
      read -p "$MSG_FORMAT_PROMPT" -r formato
      while [[ "$formato" != "btrfs" && "$formato" != "ext4" ]]; do
        echo "$MSG_INVALID_FORMAT"
        read -p "$MSG_FORMAT_PROMPT" -r formato
      done
      ;;
    bootloader) bootloader=$(prompt_for_bootloader) ;;
    *) echo "$MSG_INVALID_OPTION" ;;
    esac
  fi
done

echo "$MSG_CONFIG_CONFIRMED"

# Salva tudo no plugin YAML
plugin_set_value "particoes.root.device" "/dev/$root_dev"
plugin_set_value "particoes.root.label" "$root_label"
plugin_set_value "particoes.root.formato" "$formato"

plugin_set_value "particoes.home.device" "/dev/$home_dev"
plugin_set_value "particoes.home.label" "$home_label"

plugin_set_value "particoes.boot.device" "/dev/$boot_dev"
plugin_set_value "particoes.boot.label" "$boot_label"

plugin_set_value "particoes.swap.device" "/dev/$swap_dev"
plugin_set_value "particoes.swap.label" "$swap_label"
plugin_set_value "particoes.device" "/dev/$disco"

plugin_set_value "bootloader" "$bootloader"

# Salva variáveis de ambiente para scripts subsequentes, se necessário
set_env_var "DISCO" "$disco"
