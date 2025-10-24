bash scripts/ZA-Lang.sh

bash scripts/A-particionamento.sh

bash scripts/B-reflector.sh

bash scripts/C-instalacao.sh

bash scripts/D-regiao.sh

bash scripts/E-personalizacao.sh

if [ "$FULLCODERAN" == "yes" ]; then
  ansible-playbook -vvv ./main.yaml --tags particionamento -e @Ch-obolos/"$PLUGIN"
  cp -r ./ /mnt/root/Ch-aronte/
  ansible-playbook -vvv ./main.yaml --tags instalacao -e @Ch-obolos/"$PLUGIN"
  arch-chroot /mnt ansible-playbook -vvv /root/Ch-aronte/main.yaml --tags "$CHROOT_TAGS" -e @/root/Ch-aronte/Ch-obolos/"$PLUGIN"
  arch-chroot /mnt ansible-playbook -vvv /root/Ch-aronte/main.yaml --tags region -e @/root/Ch-aronte/Ch-obolos/"$PLUGIN"
  arch-chroot /mnt ansible-playbook -vvv /root/Ch-aronte/main.yaml --tags config -e @/root/Ch-aronte/Ch-obolos/"$PLUGIN"
  arch-chroot /mnt ansible-playbook -vvv /root/Ch-aronte/main.yaml --tags bootloader,services -e @/root/Ch-aronte/Ch-obolos/"$PLUGIN"
  if [ "$DOTS_ACCEPT" == "yes" ]; then
    echo "$MSG_LOADING_DOTS"
    arch-chroot /mnt ansible-playbook -vvv /root/Ch-aronte/main.yaml --tags dotfiles -e @Ch-obolos/"$PLUGIN"
  fi
fi
