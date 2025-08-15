#!/bin/bash
if [ "$LANG" == "Portugues" ]; then
  sleep 1
  echo "tá, teu sistema tá instalado, agora bora pra parte legal"
  echo "primeiro, vamos usar ln -sf /usr/share/zoneinfo/(sua região) pra consertar esse relógio..."
  sleep 1
  echo "pesquisa aí a região de timedatectl mais próxima de você (ou não escreva nada pra deixar em SP)"
  read -p "Região: " -r region
  if [ "$region" == "" ]; then
    region="America/Sao_Paulo"
  fi
  while [ ! -f "/usr/share/zoneinfo/$region" ]; do
    echo "Região inválida! tente de novo "
    read -p "Região: " -r region
  done
  ln -sf "/usr/share/zoneinfo/$region" "/mnt/etc/localtime"

  echo "syncando o relógio com hwclock --systohc..."
  sleep 1
  arch-chroot /mnt hwclock --systohc
  echo "relógio sincronizado paizão/mãezona/patrono... eu tenho que parar de usar tanto pronome assim, vou enlouquecer"
  sleep 1

  echo "oooookay, bora pro teu locale (tua linguagem), vamo usar nano /etc/locale.gen e VOCÊ (sim, VOCÊ) vai descomentar a linha do locale que tu quiser"
  sleep 1
  echo "ah, e deixa que eu rodo o locale-gen pra você"
  read -p "tudo certo? (Y/n) " -r certo
  while [[ "$certo" != "Y" && "$certo" != "y" && "$certo" != "" ]]; do
    echo "Por favor, leia as instruções novamente."
    read -p "tudo certo? (Y/n) " -r certo
  done
  sleep 1
  nano /mnt/etc/locale.gen
  sleep 1
  arch-chroot /mnt locale-gen
  read -p "agora, me diga a linha que tu descomentou, só coloca a região, tipo 'pt_BR' ou 'en_US' e SIM, preciso das duas letras maíusculas no final. " -r lingua
  while ! grep -q "^$lingua.UTF-8" /mnt/etc/locale.gen; do
    echo "Locale '$lingua' não encontrado no locale.gen"
    read -p "Tenta de novo, com algo tipo pt_BR ou en_US: " -r lingua
  done
  touch /mnt/etc/locale.conf
  echo "LANG=$lingua.UTF-8" >/mnt/etc/locale.conf
  echo KEYMAP=br-abnt2 >/mnt/etc/vconsole.conf
  sleep 1
elif [ "$LANG" == "English" ]; then
  sleep 1
  echo "Alright, your system is installed, now let's get to the fun part"
  echo "First, we'll use ln -sf /usr/share/zoneinfo/(your region) to fix the clock..."
  sleep 1
  echo "Search for the closest timedatectl region to you (or leave it blank to set it to NY)"
  read -p "Region: " -r region
  while [ ! -f "/usr/share/zoneinfo/$region" ]; do
    echo "Invalid region! Please try again."
    read -p "Region: " -r region
  done
  if [ "$region" == "" ]; then
    region="America/New_York"
  fi
  ln -sf "/usr/share/zoneinfo/$region" "/mnt/etc/localtime"
  echo "Syncing the clock with hwclock --systohc..."
  sleep 1
  arch-chroot /mnt hwclock --systohc
  echo "Clock synced, sir/miss/gentleperson... I really need to stop using so many pronouns, it's driving me crazy"
  sleep 1
  echo "Okay, let's set your locale (language), open nano /etc/locale.gen and YOU (yes, YOU) will uncomment the line for the locale you want"
  sleep 1
  echo "Oh, and I'll run locale-gen for you"
  read -p "All set? (Y/n) " -r certo
  while [[ "$certo" != "Y" && "$certo" != "y" && "$certo" != "" ]]; do
    echo "Please read the instructions again."
    read -p "All set? (Y/n) " -r certo
  done
  sleep 1
  nano /mnt/etc/locale.gen
  sleep 1
  arch-chroot /mnt locale-gen
  read -p "Now, tell me the line you uncommented, just type the region, like 'en_US' or 'pt_BR', and YES, I need those two uppercase letters at the end. " -r lingua
  while ! grep -q "^$lingua.UTF-8" /mnt/etc/locale.gen; do
    echo "Locale '$lingua' not found in locale.gen"
    read -p "Try again, with something like en_US or pt_BR: " -r lingua
  done
  touch /mnt/etc/locale.conf
  echo "LANG=$lingua.UTF-8" >/mnt/etc/locale.conf
  echo KEYMAP=us >/mnt/etc/vconsole.conf
  sleep 1
else
  echo "Unsupported language setting."
  bash scripts/D-regiao.sh
fi
