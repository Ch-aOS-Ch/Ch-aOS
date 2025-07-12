#!/bin/bash
sleep 1
echo "///...///"
sleep 1
echo "Opa, quase que eu me esqueci de rodar o reflector, pera ae, vai ser 2 tempo"
sleep 1
echo "[sons de teclado]"
sleep 1

if ! command -v reflector &>/dev/null; then
    echo "Ai ai... não temos o reflector, deixa que eu instalo rapidão"
    pacman -S reflector
fi

echo "jesus amado, que comando grande... aliás, é esse aqui:"
sleep 0.4
echo "reflector -c br -c us --verbose --latest 25 --sort rate --save /etc/pacman.d/mirrorlist"
reflector -c br -c us --verbose --latest 25 --sort rate --save /etc/pacman.d/mirrorlist

echo "Beleza, mirrors atualizados. Bora continuar..."
echo ""
echo "Beleza, agora vou te mostrar os pacotes essenciais que serão instalados no seu sistema base:"
sleep 1
echo "---------------------------------------------------"
echo "Pacotes necessários:"
echo "  - base"
echo "  - base-devel"
echo "  - linux"
echo "  - linux-firmware"
echo "  - linux-headers"
echo "  - reflector"
echo "  - refind"
echo "  - nano"
echo "  - networkmanager"
echo "  - openssh"
echo "---------------------------------------------------"
sleep 1
read -p "Tudo certo com essa lista? (Y/n) " ok
while [[ "$ok" != "Y" && "$ok" != "y" && "$ok" != "" ]]; do
    echo "Bom, se não tá tudo certo, tu vai ter que editar esse script aí sozinho mano..."
    read -p "Agora tá tudo certo? (Y/n) " ok
done
