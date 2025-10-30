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
	echo "$MSG_SEPARATOR"

	read -p "$MSG_DISK_PROMPT" -r disco
	while [[ -z "$disco" || ! -b "/dev/$disco" ]]; do
		echo "$MSG_INVALID_DISK"
		read -p "$MSG_DISK_PROMPT" -r disco
	done
	plugin_set_value "particoes.disk" "/dev/$disco"
	yq -iy '.particoes.partitions = []' "Ch-obolos/$PLUGIN"

	# --- Partições Obrigatórias ---
	echo "$MSG_CONFIGURING_BOOT_PARTITION"
	read -p "$MSG_PROMPT_BOOT_PART_NUMBER" boot_part
	read -p "$MSG_PROMPT_BOOT_PART_SIZE" boot_size
	read -p "$MSG_PROMPT_BOOT_PART_LABEL" boot_name
	add_partition_to_plugin "$boot_name" "$boot_size" "vfat" "$boot_part" "/boot" "boot"

	echo "$MSG_CONFIGURING_ROOT_PARTITION"
	read -p "$MSG_PROMPT_ROOT_PART_NUMBER" root_part
	read -p "$MSG_PROMPT_ROOT_PART_SIZE" root_size
	read -p "$MSG_PROMPT_ROOT_PART_LABEL" root_name
	read -p "$MSG_PROMPT_ROOT_PART_FORMAT" root_type
	add_partition_to_plugin "$root_name" "$root_size" "$root_type" "$root_part" "/" "root"

	# --- Partições Opcionais ---
	read -rp "$MSG_WANT_SWAP_PARTITION" want_swap
	if [[ "$want_swap" != "n" && "$want_swap" != "N" ]]; then
		echo "$MSG_CONFIGURING_SWAP_PARTITION"
		read -p "$MSG_PROMPT_SWAP_PART_NUMBER" swap_part
		read -p "$MSG_PROMPT_SWAP_PART_SIZE" swap_size
		read -p "$MSG_PROMPT_SWAP_PART_LABEL" swap_name
		add_partition_to_plugin "$swap_name" "$swap_size" "linux-swap" "$swap_part" "none" "swap"
	fi

	read -rp "$MSG_WANT_HOME_PARTITION" want_home
	if [[ "$want_home" != "n" && "$want_home" != "N" ]]; then
		echo "$MSG_CONFIGURING_HOME_PARTITION"
		read -p "$MSG_PROMPT_HOME_PART_NUMBER" home_part
		read -p "$MSG_PROMPT_HOME_PART_SIZE" home_size
		read -p "$MSG_PROMPT_HOME_PART_LABEL" home_name
		add_partition_to_plugin "$home_name" "$home_size" "ext4" "$home_part" "/home" "home"
	fi

	# --- Loop de Verificação e Correção ---
	echo "$MSG_SEPARATOR"
	echo "$MSG_GENERATED_PARTITION_CONFIG"
	yq . "Ch-obolos/$PLUGIN" | jq '.particoes'
	echo "$MSG_SEPARATOR"
	read -p "$MSG_CONFIRM_PROMPT" -r confirmacao

done

read -p "$MSG_BOOTLOADER_PROMPT" bootloader
plugin_set_value "bootloader" "$bootloader"

echo "$MSG_CONFIG_CONFIRMED"
echo "$MSG_ANSIBLE_APPLYING_CHANGES"
ansible-playbook ./main.yaml --tags particionamento -e @Ch-obolos/"$PLUGIN"
set_env_var "PARTITIONED" "true"
