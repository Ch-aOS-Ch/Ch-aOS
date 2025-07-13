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
sleep 1
