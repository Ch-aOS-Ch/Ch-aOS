#!/bin/bash
set -e
set -a
source respostas.env
set +a

# ==============================================================================
# SETUP DE IDIOMA E VARIÁVEIS
# ==============================================================================
case "$LANGC" in
"Portugues")
  MSG_START="belezinha belezinha, agora é a parte final, tá preparado?"
  MSG_CONFIGURING="Configurando o bootloader via Ansible..."
  MSG_ENABLE_NETWORK="Habilitando o NetworkManager para iniciar com o sistema..."
  MSG_GOODBYE_1="Ok, meu trabalho aqui tá feito, agora é contigo. Em teoria, é só reiniciar."
  MSG_GOODBYE_2="Se der ruim, a culpa não é minha! Brincadeira, tentei fazer o script redondinho."
  MSG_GOODBYE_3="Se encontrar um bug, abra uma issue no GitHub. Obrigado por usar o Ch-aronte!"
  ;;
"English")
  MSG_START="Alright, now for the final part, are you ready?"
  MSG_CONFIGURING="Configuring the bootloader via Ansible..."
  MSG_ENABLE_NETWORK="Enabling NetworkManager to start on boot..."
  MSG_GOODBYE_1="Alright, my job here is done, now it's up to you. In theory, you just need to reboot."
  MSG_GOODBYE_2="If something goes wrong, it's not my fault! Just kidding, I tried to make the script solid."
  MSG_GOODBYE_3="If you find a bug, open an issue on GitHub. Thanks for using Ch-aronte!"
  ;;
*)
  echo "Unsupported language setting."
  exit 1
  ;;
esac

# ==============================================================================
# FLUXO PRINCIPAL DO SCRIPT
# ==============================================================================
echo "$MSG_START"
sleep 1

echo "$MSG_CONFIGURING"
# Garante que o ambiente do chroot tenha o código mais recente
cp -r . /mnt/root/Ch-aronte/
arch-chroot /mnt ansible-playbook -vvv /root/Ch-aronte/main.yaml --tags bootloader -e @/root/Ch-aronte/plugins/"$PLUGIN"
rm -rf /mnt/root/Ch-aronte/

# Garante que o NetworkManager está no plugin e executa a role de serviços
echo "$MSG_ENABLE_SERVICES"
yq -iy '.services |= (select(.) // []) | . + [{"name": "NetworkManager", "state": "started", "enabled": true}] | unique_by(.name)' "plugins/$PLUGIN"

# Sincroniza o estado do plugin e executa a role
cp -r . /mnt/root/Ch-aronte/
arch-chroot /mnt ansible-playbook -vvv /root/Ch-aronte/main.yaml --tags services -e @/root/Ch-aronte/plugins/"$PLUGIN"
rm -rf /mnt/root/Ch-aronte/


echo "---------------------------------------------------"
echo "$MSG_GOODBYE_1"
echo "$MSG_GOODBYE_2"
echo "$MSG_GOODBYE_3"
