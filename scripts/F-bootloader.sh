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
  MSG_START="belezinha belezinha, agora é a parte fudida, tá preparado?"
  MSG_CONFIGURING_REFIND="vamo configurar teu refind (UEFI)..."
  MSG_CONFIGURING_GRUB="Beleza, detectei um sistema BIOS. Vamo configurar o GRUB..."
  MSG_ROOT_LABEL_PROMPT="me dá um nome daora aí pro teu partição de root (ex: ARCH_ROOT): "
  MSG_GRUB_INSTALL="Instalando o GRUB no disco /dev/${DISCO}..."
  MSG_GRUB_CONFIG="Gerando o arquivo de configuração do GRUB..."
  MSG_ENABLE_NETWORK="Habilitando o NetworkManager para iniciar com o sistema..."
  MSG_GOODBYE_1="Ok, meu trabalho aqui tá feito, agora é contigo. Em teoria, é só reiniciar."
  MSG_GOODBYE_2="Se der ruim, a culpa não é minha! Brincadeira, tentei fazer o script redondinho."
  MSG_GOODBYE_3="Se encontrar um bug, abra uma issue no GitHub. Obrigado por usar o Ch-aronte!"
  ;;
"English")
  MSG_START="Alright, now for the tricky part, are you ready?"
  MSG_CONFIGURING_REFIND="Let's configure your refind (UEFI)..."
  MSG_CONFIGURING_GRUB="Okay, BIOS system detected. Let's configure GRUB..."
  MSG_ROOT_LABEL_PROMPT="Give a cool name for your root partition label (e.g., ARCH_ROOT): "
  MSG_GRUB_INSTALL="Installing GRUB on disk /dev/${DISCO}..."
  MSG_GRUB_CONFIG="Generating GRUB configuration file..."
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
sleep 1
hostname="$(cat /mnt/etc/hostname)"
echo "$MSG_START"

# AQUI ESTÁ A LÓGICA DE DECISÃO PRINCIPAL
if [ "$FIRMWARE" == "UEFI" ]; then
  # --- LÓGICA PARA UEFI (refind) ---
  echo "$MSG_CONFIGURING_REFIND"
  arch-chroot /mnt refind-install

  read -p "$MSG_ROOT_LABEL_PROMPT" -r root_label

  # Adiciona a entrada de boot customizada no refind.conf
  if ! grep -q "Ch-aronte" /mnt/boot/efi/refind/refind.conf; then
    cat <<EOF >>/mnt/boot/efi/refind/refind.conf

# ---------------------------------------------------------
# Entrada adicionada automaticamente pelo script Ch-aronte
# ---------------------------------------------------------
menuentry "$hostname" {
    icon /EFI/refind/icons/os_arch.png
    volume "$root_label"
    loader /vmlinuz-linux
    initrd /initramfs-linux.img
    options "root=LABEL=$root_label rw add_efi_memmap"
    submenuentry "Fallback" {
        initrd /initramfs-linux-fallback.img
    }
    submenuentry "Boot to Terminal" {
        add_options "systemd.unit=multi-user.target"
    }
}
EOF
  fi

  echo "Definindo o label da partição root para '$root_label'..."
  if [[ "$FORMATO_ROOT" == "btrfs" ]]; then
    btrfs filesystem label "$ROOTP" "$root_label"
  else
    e2label "$ROOTP" "$root_label"
  fi

else
  # --- LÓGICA PARA BIOS (grub) ---
  echo "$MSG_CONFIGURING_GRUB"
  sleep 1
  echo "$MSG_GRUB_INSTALL"
  arch-chroot /mnt grub-install --target=i386-pc "/dev/${DISCO}"
  sleep 1
  echo "$MSG_GRUB_CONFIG"
  arch-chroot /mnt grub-mkconfig -o /boot/grub/grub.cfg
  sleep 1
fi

# --- PASSOS FINAIS COMUNS A AMBOS ---
echo "$MSG_ENABLE_NETWORK"
arch-chroot /mnt systemctl enable NetworkManager

echo "---------------------------------------------------"
echo "$MSG_GOODBYE_1"
echo "$MSG_GOODBYE_2"
echo "$MSG_GOODBYE_3"
