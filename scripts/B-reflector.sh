#!/bin/bash
if [ "$LANGC" == "Portugues" ]; then
  sleep 1
  echo "///...///"
  sleep 1
  echo "Opa, quase que eu me esqueci de rodar o reflector, pera ae, vai ser 2 tempo"
  sleep 1
  echo "[sons de teclado]"
  sleep 1

  if ! command -v reflector &>/dev/null; then
    echo "Ai ai... não temos o reflector, deixa que eu instalo rapidão"
    pacman -Sy reflector
  fi

  echo "jesus amado, que comando grande... aliás, é esse aqui:"
  sleep 0.4
  echo "reflector -c br -c us --verbose --latest 25 --sort rate --save /etc/pacman.d/mirrorlist"
  reflector -c br -c us --verbose --latest 25 --sort rate --save /etc/pacman.d/mirrorlist
  sleep 1

elif [ "$LANGC" == "English" ]; then
  echo "///...///"
  sleep 1
  echo "Oh, I almost forgot to run reflector, hold on, it will be quick"
  sleep 1
  echo "[typing sounds]"
  sleep 1
  if ! command -v reflector &>/dev/null; then
    echo "Oh no... reflector is not installed, let me install it real quick, 1 sec"
    pacman -Sy reflector
  fi
  echo "Damn, that's a long command... here it is:"
  sleep 0.4
  echo "reflector -c eu -c us --verbose --latest 25 --sort rate --save /etc/pacman.d/mirrorlist"
  reflector -c br -c us --verbose --latest 25 --sort rate --save /etc/pacman.d/mirrorlist
else
  echo "Unsupported language setting."
  bash scripts/B-reflector.sh
fi
