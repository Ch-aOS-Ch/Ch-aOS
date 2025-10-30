#!/bin/bash
set -e

source ./lib/ui.sh
source ./lib/plugin.sh
source ./scripts/resources.sh
set -a
source ./respostas.env
set +a

# --- FLUXO PRINCIPAL DO SCRIPT ---
echo "$MSG_CONTINUE"
echo "$MSG_SHOW_PKGS"
sleep 1
echo "---------------------------------------------------"
echo "Pacotes necessários / Required packages:"
echo "  - base, base-devel, linux, linux-firmware, linux-headers"
echo "  - reflector, bootloader(grub ou refind), nano, networkmanager, openssh"
echo "---------------------------------------------------"
sleep 1

# Garante que a chave 'pacotes' exista como uma lista no plugin
yq -iy '.pacotes |= (select(.) // [])' "Ch-obolos/$PLUGIN"

add_pkg="n"
read -p "$MSG_WANT_MORE" -r add_pkg
while [[ "$add_pkg" != "n" && "$add_pkg" != "N" ]]; do
	read -p "$MSG_PKG_NAME" -r pacote
	while ! pacman -Ss "$pacote" >/dev/null 2>&1; do
		echo "$MSG_NOT_FOUND"
		read -p "$MSG_TRY_AGAIN" -r pacote
	done

	plugin_add_to_list_unique "pacotes" "$pacote"
	echo "$MSG_ADDING $pacote..."

	read -p "$MSG_ANY_MORE" -r add_pkg
done

ansible-playbook ./main.yaml --tags instalacao -e @Ch-obolos/"$PLUGIN"
systemctl daemon-reload
plugin_set_value "repos.managed.core" "true"
repos_update

CHROOT_TAGS="repos"
if [[ "$add_pkg" != "n" && "$add_pkg" != "N" ]]; then
	export CHROOT_TAGS="$CHROOT_TAGS,pkgs"
fi
set_env_var "INSTALLED" "true"
