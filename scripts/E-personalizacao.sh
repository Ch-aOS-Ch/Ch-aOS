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

chmod +x ./scripts/F-bootloader.sh
bash ./scripts/F-bootloader.sh
