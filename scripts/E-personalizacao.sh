#!/bin/bash
set -a
source respostas.env
set +a

# ==============================================================================
# SETUP DE IDIOMA E VARIÁVEIS
# ==============================================================================
case "$LANGC" in
"Portugues")
  MSG_HOSTNAME_PROMPT="ok, me dá um nome pro seu pc aí... e pelo amor de deus, me dá um nome bonito... "
  MSG_INVALID_HOSTNAME="Nome inválido. Só letras, números, ponto ou hífen. Tenta de novo aí oh jegue: "
  MSG_RUNNING_MKINITCPIO="rodando mkinitcpio -P..."
  MSG_MKINITCPIO_DONE="aí sim porra, rodou. Agora vamo settar tua senha de root (sem 1234 seu jegue)"
  MSG_SET_USER="agora me fala teu user, vamo criar e tacar ele lá no sudoers"
  MSG_USERNAME_PROMPT="Nome do teu usuário: "
  MSG_INVALID_USERNAME="Nome de usuário inválido. Deve começar com letra minúscula e conter apenas letras minúsculas, números, _ ou -. Mals aí "
  ;;
"English")
  MSG_HOSTNAME_PROMPT="Alright, give your PC a name... and please, make it a nice one... "
  MSG_INVALID_HOSTNAME="Invalid name. Only letters, numbers, dot or hyphen. Try again: "
  MSG_RUNNING_MKINITCPIO="Running mkinitcpio -P..."
  MSG_MKINITCPIO_DONE="ALRIGHT DAMMIT, it's done. Now let's set your root password (no 1234, you fool)."
  MSG_SET_USER="Now tell me your username, let's create it and add it to the sudoers."
  MSG_USERNAME_PROMPT="Your username: "
  MSG_INVALID_USERNAME="Invalid username. Must start with a lowercase letter and contain only lowercase letters, numbers, _ or -. Try again: "
  ;;
*)
  echo "Language not recognized. Exiting."
  exit 1
  ;;
esac

# ==============================================================================
# FLUXO PRINCIPAL DO SCRIPT
# ==============================================================================

# --- Hostname ---
read -p "$MSG_HOSTNAME_PROMPT" -r hostname
while [[ -z "$hostname" || "$hostname" =~ [^a-zA-Z0-9.-] ]]; do
  read -p "$MSG_INVALID_HOSTNAME" -r hostname
done
echo "$hostname" >/mnt/etc/hostname
sleep 1

# --- Initramfs ---
echo "$MSG_RUNNING_MKINITCPIO"
arch-chroot /mnt mkinitcpio -P
echo ""
sleep 1

# --- Senha do Root ---
echo "$MSG_MKINITCPIO_DONE"
arch-chroot /mnt passwd
sleep 1

# --- Criação do Usuário ---
echo "$MSG_SET_USER"
read -p "$MSG_USERNAME_PROMPT" -r username

# A VALIDAÇÃO ADICIONADA ESTÁ AQUI
while [[ -z "$username" || ! "$username" =~ ^[a-z_][a-z0-9_-]*$ ]]; do
  read -p "$MSG_INVALID_USERNAME" -r username
done

arch-chroot /mnt useradd -m -g users -G wheel -s /bin/bash "$username"
echo "Agora defina a senha para o usuário '$username':"
arch-chroot /mnt passwd "$username"

# --- Copia os scripts para o novo sistema ---
echo "Copiando os scripts de instalação para /home/$username/Ch-aronte..."
rm -rf ~/Ch-aronte/.git
cp -r ~/Ch-aronte "/mnt/home/$username/Ch-aronte"
# Garante que o novo usuário seja o dono dos arquivos copiados
arch-chroot /mnt chown -R "$username:$username" "/home/$username/Ch-aronte"
sleep 1

# ==============================================================================
# LÓGICA COMPARTILHADA FINAL
# (Esta parte já estava ótima!)
# ==============================================================================

# --- Habilita o Sudo para o grupo 'wheel' ---
echo "Habilitando privilégios de superusuário (sudo) para o novo usuário..."
if ! grep -q "^%wheel ALL=(ALL:ALL) ALL" /mnt/etc/sudoers; then
  # Usa sed para descomentar a linha do wheel
  sed -i 's/^# %wheel ALL=(ALL:ALL) ALL/%wheel ALL=(ALL:ALL) ALL/' /mnt/etc/sudoers
fi

# --- Encadeia o próximo script ---
echo "Configuração finalizada. Passando para a instalação do bootloader..."
chmod +x scripts/F-bootloader.sh
bash scripts/F-bootloader.sh
