#!/bin/bash
set -a
source respostas.env
set +a

case "$LANGC" in
"Portugues")
  MSG_LOADING_DOTS="Fecho, carregando suas dots."
  ;;
"English")
  MSG_LOADING_DOTS="Ight, loading ya dots."
  ;;
*)
  echo "LANGUAGE NOT RECOGNIZED, PLEASE USE EITHER ENGLISH OR PORTUGUESE."
  ;;

esac

echo "$MSG_LOADING_DOTS"
sleep 0.5
arch-chroot /mnt ansible-playbook -vvv /root/Ch-aronte/main.yaml --tags dotfiles
