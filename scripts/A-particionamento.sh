#!/bin/bash
source scripts/resources.sh
timedatectl
loadkeys br-abnt2
mkdir -p "tmp/.ansible-${USER}/tmp"

sleep 1
echo "Preparando particionamento..."
sleep 1
echo "3..."
sleep 1
echo "2..."
sleep 1
echo "1..."
echo "Alô alô??? alguém aí????? beleza, tamo começando aqui, se prepara pra iniciar"
echo ""
echo "Vamos começar a particionar o disco"
echo ""
echo "vamos usar o comando cfdisk, então se certifique de se preparar."
echo ""
echo "recomendo usar 4 partições: root, home, swap e boot."
echo "boot = 1G com tipo EFI system | root = 40G+ / Linux root(x86_64) | swap = 4G+ / linux swap | home = resto / linux home"
echo "Finalize com 'write' ou 'gravar' no cfdisk pra aplicar as alterações."
echo "---------------------------------------------------"

read -p "Você entendeu tudo (digite N para confirmar)? (y/N) " -r resposta
while [[ "$resposta" == "Y" || "$resposta" == "y" || "$resposta" == "" ]]; do
  echo "Por favor, leia as instruções novamente e PARA DE FICAR SÓ DANDO ENTER!"
  read -p "Você entendeu tudo? (y/N) " -r resposta
done

echo "Continuando..."
sleep 1
echo "---------------------------------------------------"
lsblk
echo "---------------------------------------------------"

read -p "Digite o disco que vai ser particionado (ex: sda): " -r disco
while [[ -z "$disco" || ! -b "/dev/$disco" ]]; do
  echo "Por favor, digite um disco válido."
  read -p "Digite o disco que vai ser particionamento (ex: sda): " -r disco
done

envfile="respostas.env"
touch "$envfile"

set_env_var "DISCO" "$disco"
cfdisk "/dev/$disco"

read -p "qual a tua Partição ROOT? (ex: sda2): " -r root
while [[ -z "$root" || ! -b "/dev/$root" ]]; do
  echo "Por favor, digite uma partição válida."
  read -p "qual a tua Partição ROOT? (ex: sda2): " -r root
done

read -p "qual a tua Partição HOME? (ex: sda4): " -r home
while [[ -z "$home" || ! -b "/dev/$home" ]]; do
  echo "Por favor, digite uma partição válida."
  read -p "qual a tua Partição HOME? (ex: sda4): " -r home
done

read -p "qual a tua Partição BOOT? (ex: sda1): " -r boot
while [[ -z "$boot" || ! -b "/dev/$boot" ]]; do
  echo "Por favor, digite uma partição válida."
  read -p "qual a tua Partição BOOT? (ex: sda1): " -r boot
done

read -p "qual a tua Partição SWAP? (ex: sda3): " -r swap
while [[ -z "$swap" || ! -b "/dev/$swap" ]]; do
  echo "Por favor, digite uma partição válida."
  read -p "qual a tua Partição SWAP? (ex: sda3): " -r swap
done

echo "O formato da partição root pode ser btrfs ou ext4."
echo "btrfs ajuda a compactar mais seu disco root, mas piora performance em jogos, por exemplo, enquanto ext4 é mais tradicional."
read -p "qual formato você quer sua particao root?(btrfs/ext4) " -r formato
while [[ "$formato" != "btrfs" && "$formato" != "ext4" ]]; do
  echo "Formato inválido. Por favor, escolha btrfs ou ext4."
  read -p "qual formato você quer sua particao root?(btrfs/ext4) " -r formato
done

set_env_var "FORMATO_ROOT" "$formato"
set_env_var "ROOT" "/dev/$root"
set_env_var "HOME" "/dev/$home"
set_env_var "BOOT" "/dev/$boot"
set_env_var "SWAP" "/dev/$swap"

echo ""
echo "Partições salvas:"
echo "ROOT=$root"
echo "HOME=$home"
echo "BOOT=$boot"
echo "SWAP=$swap"
echo "Disco principal: $disco"
echo "Formato da partição root: $formato"
echo "---------------------------------------------------"
#read -p "Confirma? (Y/n) " confirmacao
#while [[ "$confirmacao" != "Y" && "$confirmacao" != "y" && "$confirmacao" != "" ]]; do
# echo "Por favor, confirme as partições."
# echo "ROOT=$root"
# echo "HOME=$home"
# echo "BOOT=$boot"
# echo "SWAP=$swap"
# echo "Disco principal: $disco"
# echo "Formato da partição root: $formato"
# read -p "qual a partição atual da que quer mudar? (ex: sda2): " particao_atual
# read -p "para qual você deseja mudar?(sda2, sda1, etc)" mudanca
# read -p "Confirma? (Y/n) " confirmacao
#done

set -a
source ./respostas.env
set +a

# Chamada para o playbook de particionamento
ansible-playbook -vvv ./main.yaml --tags particionamento
genfstab -U /mnt >>/mnt/etc/fstab
chmod +x ./scripts/B-reflector.sh
bash ./scripts/B-reflector.sh
