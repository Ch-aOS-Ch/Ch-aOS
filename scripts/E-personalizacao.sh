#!/bin/bash
set -a
source respostas.env
set +a
if [ "$LANGC" = Portugues ]; then
  read -p "ok, me dá um nome pro seu pc aí... e pelo amor de deus, me dá um nome bonito... " -r nome_pc
  while [[ -z "$nome_pc" || "$nome_pc" =~ [^a-zA-Z0-9.-] ]]; do
    read -p "Nome inválido. Só letras, números, ponto ou hífen. Tenta de novo aí oh jegue: " -r nome_pc
  done
  echo "$nome_pc" >/mnt/etc/hostname
  sleep 1
  echo "rodando mkinitcpio -P..."
  sleep 1
  arch-chroot /mnt mkinitcpio -P
  echo ""
  echo "aí sim porra, rodou. Agora vamo settar tua senha de root (sem 1234 seu jegue)"
  sleep 1
  arch-chroot /mnt passwd
  sleep 1
  echo "agora me fala teu user, vamo criar e tacar ele lá no sudoers"
  sleep 1
  read -p "Nome do teu usuário: " -r nome_user
  arch-chroot /mnt useradd -m -g users -G wheel -s /bin/bash "$nome_user"
  arch-chroot /mnt passwd "$nome_user"
elif [ "$LANGC" = English ]; then
  read -p "Alright, give your PC a name... and please, make it a nice one... " -r pc_name
  while [[ -z "$pc_name" || "$pc_name" =~ [^a-zA-Z0-9.-] ]]; do
    read -p "Invalid name. Only letters, numbers, dot or hyphen. Try again: " -r pc_name
  done
  echo "$pc_name" >/mnt/etc/hostname
  sleep 1
  echo "Running mkinitcpio -P..."
  sleep 1
  arch-chroot /mnt mkinitcpio -P
  echo ""
  echo "ALRIGHT DAMMIT, it's done. Now let's set your root password (no 1234, dumb, dumb, idiot)."
  sleep 1
  arch-chroot /mnt passwd
  sleep 1
  echo "Now tell me your username, let's create it and add it to the sudoers."
  sleep 1
  read -p "Your username: " -r user_name
  arch-chroot /mnt useradd -m -g users -G wheel -s /bin/bash "$user_name"
  arch-chroot /mnt passwd "$user_name"
else
  echo "Language not recognized. Please set LANGC to either 'Portugues' or 'English'."
  bash scripts/E-personalizacao.sh
fi
if ! grep -q "^%wheel ALL=(ALL:ALL) ALL" /mnt/etc/sudoers; then
  sed -i 's/^# %wheel ALL=(ALL:ALL) ALL/%wheel ALL=(ALL:ALL) ALL/' /mnt/etc/sudoers
fi
