#!/bin/bash
set -e
set -a
source lib/ui.sh
source lib/plugin.sh
source respostas.env
set +a
source lib/ui.sh

yq -iy '.mirrors.countries = []' "Ch-obolos/$PLUGIN"
case $LANGC in
"Portugues")
	plugin_add_to_list "mirrors.countries" "br"
	plugin_add_to_list "mirrors.countries" "us"
	;;
"English")
	plugin_add_to_list "mirrors.countries" "us"
	plugin_add_to_list "mirrors.countries" "eu"
	;;
esac
plugin_set_value "mirrors.count" "25"

sleep 1
echo "///...///"
sleep 1
echo "$MSG_ALMOST_FORGOT"
sleep 1
echo "$MSG_TYPING_SOUNDS"
sleep 1
REFLECTOR_CMD="reflector $REFLECTOR_COUNTRIES --verbose --latest 25 --sort rate --save /etc/pacman.d/mirrorlist"
echo "$MSG_COMMAND_IS"
sleep 0.4
echo "$REFLECTOR_CMD"

ansible-playbook main.yaml --tags reflector -e @Ch-obolos/"$PLUGIN"

echo "$FINALIZESC"
set_env_var "REFLECTORED" "true"
