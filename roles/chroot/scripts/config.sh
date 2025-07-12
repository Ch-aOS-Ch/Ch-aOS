sleep 1
echo "tá, teu sistema tá instalado, agora bora pra parte legal"
echo "primeiro, vamos usar ln -sf /usr/share/zoneinfo/(sua região) pra consertar esse relógio..."
sleep 1
echo "pesquisa aí a região de timedatectl mais próxima de você (ou não escreva nada pra deixar em SP)"
read -p "Região: " region
if [ "$region" == "" ]; then
    region="America/Sao_Paulo"
fi
while [ ! -f "/usr/share/zoneinfo/$region" ]; do
    echo "Região inválida! tente de novo "
    read -p "Região: " region
done
ln -sf "/usr/share/zoneinfo/$region" "/mnt/etc/localtime"

echo "syncando o relógio com hwclock --systohc..."
sleep 1
arch-chroot /mnt hwclock --systohc; echo "relógio sincronizado paizão/mãezona/patrono... eu tenho que parar de usar tanto pronome assim, vou enlouquecer"
sleep 1

echo "oooookay, bora pro teu locale (tua linguagem), vamo usar nano /etc/locale.gen e VOCÊ (sim, VOCÊ) vai descomentar a linha do locale que tu quiser"
sleep 1
echo "ah, e deixa que eu rodo o locale-gen pra você"
sleep 1
nano /mnt/etc/locale.gen
sleep 1
arch-chroot /mnt locale-gen
read -p "agora, me diga a linha que tu descomentou, só coloca a região, tipo 'pt_BR' ou 'en_US' e SIM, preciso das duas letras maíusculas no final. " lingua
while ! grep -q "^$lingua.UTF-8" /mnt/etc/locale.gen; do
    echo "Locale '$lingua' não encontrado no locale.gen"
    read -p "Tenta de novo, com algo tipo pt_BR ou en_US: " lingua
done
touch /mnt/etc/locale.conf; echo "LANG=$lingua.UTF-8" > /mnt/etc/locale.conf
echo KEYMAP=br-abnt2 > /mnt/etc/vconsole.conf
sleep 1

read -p "ok, me dá um nome pro seu pc aí... e pelo amor de deus, me dá um nome bonito" nome_pc
while [[ -z "$nome_pc" || "$nome_pc" =~ [^a-zA-Z0-9.-] ]]; do
    read -p "Nome inválido. Só letras, números, ponto ou hífen. Tenta de novo aí oh jegue: " nome_pc
done
echo "$nome_pc" > /mnt/etc/hostname
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
read -p "Nome teu usuário: " nome_user
arch-chroot /mnt useradd -m -g users -G wheel -s /bin/bash "$nome_user"
arch-chroot /mnt passwd "$nome_user"
if ! grep -q "^%wheel ALL=(ALL:ALL) ALL" /mnt/etc/sudoers; then
    sed -i 's/^# %wheel ALL=(ALL:ALL) ALL/%wheel ALL=(ALL:ALL) ALL/' /mnt/etc/sudoers
fi

echo "belezinha belezinha, agora é a parte fudida, tá preparado?"
echo "vamo configurar teu refind."
arch-chroot /mnt refind-install
read -p "me dá um nome daora aí pro teu disco de root" nome_root
cat <<EOF >> /mnt/boot/refind/refind.conf

# ---------------------------------------------------------
# Entrada adicionada automaticamente pelo script Ch-aronte
# ---------------------------------------------------------

menuentry '$nome_pc' {
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
read -p "qual era tua partição de root mesmo?" root
read -p "e tu usava btrfs ou nem (y/N)? " btrfs
if [[ $btrfs == "y" ]]; then
    btrfs filesystem label /dev/$root "$nome_root"
else
    e2label "/dev/$root" "$nome_root"
fi
