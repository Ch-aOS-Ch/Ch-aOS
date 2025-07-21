#!/bin/bash
sleep 1
nome_pc="$(cat /mnt/etc/hostname)"
echo "belezinha belezinha, agora é a parte fudida, tá preparado?"
echo "vamo configurar teu refind."
arch-chroot /mnt refind-install
read -p -r "me dá um nome daora aí pro teu disco de root" nome_root
cat <<EOF >>/mnt/boot/refind/refind.conf

# ---------------------------------------------------------
# Entrada adicionada automaticamente pelo script Ch-aronte
# ---------------------------------------------------------

menuentry "$nome_pc" {
    icon /EFI/refind/icons/os_arch.png
    volume $nome_pc
    loader /vmlinuz-linux
    initrd /initramfs-linux.img
    options root=LABEL=$nome_root rw add_efi_memmap
    submenuentry 'fallback' {
        initrd /initramfs-linux-fallback.img
    }
    submenuentry 'bootar pro terminal' {
        add_options 'systemd.unit=multi-user.target'
    }
}
EOF

lsblk
echo ""
read -p -r "qual era tua partição de root mesmo?" root
read -p -r "e tu usava btrfs ou nem (y/N)? " btrfs
if [[ $btrfs == "y" ]]; then
  btrfs filesystem label "/dev/$root" "$nome_root"
else
  e2label "/dev/$root" "$nome_root"
fi
arch-chroot /mnt systemctl enable NetworkManager
