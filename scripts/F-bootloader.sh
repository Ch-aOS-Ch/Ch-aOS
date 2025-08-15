#!/bin/bash
set -a
source respostas.env
set +a
if [ "$LANGC" = Portugues ]; then
  sleep 1
  nome_pc="$(cat /mnt/etc/hostname)"
  echo "belezinha belezinha, agora é a parte fudida, tá preparado?"
  echo "vamo configurar teu refind."
  arch-chroot /mnt refind-install
  read -p "me dá um nome daora aí pro teu disco de root: " -r nome_root
  cat <<EOF >>/mnt/boot/efi/refind/refind.conf

# ---------------------------------------------------------
# Entrada adicionada automaticamente pelo script Ch-aronte
# ---------------------------------------------------------

menuentry "$nome_pc" {
    icon /EFI/refind/icons/os_arch.png
    volume $nome_pc
    loader /vmlinuz-linux
    initrd /initramfs-linux.img
    options "root=LABEL=$nome_root rw add_efi_memmap"
    submenuentry "fallback" {
        initrd /initramfs-linux-fallback.img
    }
    submenuentry "bootar pro terminal" {
        add_options "systemd.unit=multi-user.target"
    }
}
EOF

  lsblk
  echo ""
  read -p "qual era tua partição de root mesmo? " -r root
  read -p "e tu usava btrfs ou nem (y/N)? " -r btrfs
  if [[ $btrfs == "y" ]]; then
    btrfs filesystem label "/dev/$root" "$nome_root"
  else
    e2label "/dev/$root" "$nome_root"
  fi
  arch-chroot /mnt systemctl enable NetworkManager
  echo "Ok, meu trabalho aqui tá feito, agora é contigo, se vira nos 30. Em teoria, é só reiniciar"
  echo "mas se der ruim, aí é contigo, tentei fazer o script redondinho e o mais fácil"
  echo "e se der ruim, manda mensagem lá no github que eu vou tentar corrigir o bug, mas vc que tem que identificar o problema"
  echo "Obrigado por usar o Ch-aronte, espero que tenha gostado"else
  echo "Unsupported language setting."

elif [ "$LANGC" = English ]; then
  sleep 1
  nome_pc="$(cat /mnt/etc/hostname)"
  echo "Alright, now it's the hard part, are you ready?"
  echo "Let's configure your refind."
  arch-chroot /mnt refind-install
  read -p "Give a cool name for your root disk: " -r root_name
  cat <<EOF >>/mnt/boot/efi/refind/refind.conf

# ---------------------------------------------------------
# Entry automatically added by the Ch-aronte script
# ---------------------------------------------------------

menuentry "$nome_pc" {
    icon /EFI/refind/icons/os_arch.png
    volume $nome_pc
    loader /vmlinuz-linux
    initrd /initramfs-linux.img
    options "root=LABEL=$root_name rw add_efi_memmap"
    submenuentry "fallback" {
        initrd /initramfs-linux-fallback.img
    }
    submenuentry "bootar pro terminal" {
        add_options "systemd.unit=multi-user.target"
    }
}

EOF
  lsblk
  echo ""
  read -p "What was your root partition again? " -r root
  read -p "Did you use btrfs or not (y/N)? " -r btrfs
  if [[ $btrfs == "y" ]]; then
    btrfs filesystem label "/dev/$root" "$root_name"
  else
    e2label "/dev/$root" "$root_name"
  fi
  arch-chroot /mnt systemctl enable NetworkManager
  echo "Alright, my job here is done, now it's up to you, good luck. In theory, you just need to reboot."
  echo "But if something goes wrong, it's on you, I tried to make the script as smooth and easy as possible."
  echo "If it fails, message me on GitHub and I'll try to fix the bug, but you need to identify the problem."
  echo "Thanks for using Ch-aronte, hope you liked it!"
else
  echo "Language not recognized. Please set LANGC to either 'Portugues' or 'English'."
  bash scripts/F-bootloader.sh
fi
