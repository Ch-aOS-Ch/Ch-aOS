#!/bin/bash
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
arch-chroot /mnt hwclock --systohc
echo "relógio sincronizado paizão/mãezona/patrono... eu tenho que parar de usar tanto pronome assim, vou enlouquecer"
sleep 1

echo "oooookay, bora pro teu locale (tua linguagem), vamo usar nano /etc/locale.gen e VOCÊ (sim, VOCÊ) vai descomentar a linha do locale que tu quiser"
sleep 1
echo "ah, e deixa que eu rodo o locale-gen pra você"
read -p "tudo certo? (Y/n) " certo
while [[ "$certo" != "Y" && "$certo" != "y" && "$certo" != "" ]]; do
  echo "Por favor, leia as instruções novamente."
  read -p "tudo certo? (Y/n) " certo
done
sleep 1
nano /mnt/etc/locale.gen
sleep 1
arch-chroot /mnt locale-gen
read -p "agora, me diga a linha que tu descomentou, só coloca a região, tipo 'pt_BR' ou 'en_US' e SIM, preciso das duas letras maíusculas no final. " lingua
while ! grep -q "^$lingua.UTF-8" /mnt/etc/locale.gen; do
  echo "Locale '$lingua' não encontrado no locale.gen"
  read -p "Tenta de novo, com algo tipo pt_BR ou en_US: " lingua
done
touch /mnt/etc/locale.conf
echo "LANG=$lingua.UTF-8" >/mnt/etc/locale.conf
echo KEYMAP=br-abnt2 >/mnt/etc/vconsole.conf
sleep 1
chmod +x ./scripts/E-personalizacao.sh
bash ./scripts/E-personalizacao.sh
