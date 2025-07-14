#!/bin/bash
source scripts/resources.sh
timedatectl
loadkeys br-abnt2
mkdir -p tmp/.ansible-${USER}/tmp


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
echo "boot = 1G / EFI system | root = 40G+ / Linux root(x86_64) | swap = 4G+ | home = resto"
echo "Finalize com 'write' ou 'gravar' no cfdisk pra aplicar as alterações."
echo "---------------------------------------------------"

read -p "Você entendeu tudo? (Y/n) " resposta
while [[ "$resposta" != "Y" && "$resposta" != "y" && "$resposta" != "" ]]; do
    echo "Por favor, leia as instruções novamente."
    read -p "Você entendeu tudo? (Y/n) " resposta
done

echo "Continuando..."
sleep 1
echo "---------------------------------------------------"
lsblk
echo "---------------------------------------------------"

read -p "Digite o disco que vai ser particionamento (ex: sda): " disco
while [[ -z "$disco" || ! -b "/dev/$disco" ]]; do
    echo "Por favor, digite um disco válido."
    read -p "Digite o disco que vai ser particionamento (ex: sda): " disco
done

# Criar/respeitar respostas.env
envfile="respostas.env"
touch "$envfile"

set_env_var "DISCO" "$disco"
cfdisk "/dev/$disco"

read -p "qual a tua Partição ROOT? (ex: sda2): " root
while [[ -z "$root" || ! -b "/dev/$root" ]]; do
    echo "Por favor, digite uma partição válida."
    read -p "qual a tua Partição ROOT? (ex: sda2): " root
done

read -p "qual a tua Partição HOME? (ex: sda4): " home
while [[ -z "$home" || ! -b "/dev/$home" ]]; do
    echo "Por favor, digite uma partição válida."
    read -p "qual a tua Partição HOME? (ex: sda4): " home
done

read -p "qual a tua Partição BOOT? (ex: sda1): " boot
while [[ -z "$boot" || ! -b "/dev/$boot" ]]; do
    echo "Por favor, digite uma partição válida."
    read -p "qual a tua Partição BOOT? (ex: sda1): " boot
done

read -p "qual a tua Partição SWAP? (ex: sda3): " swap
while [[ -z "$swap" || ! -b "/dev/$swap" ]]; do
    echo "Por favor, digite uma partição válida."
    read -p "qual a tua Partição SWAP? (ex: sda3): " swap
done

read -p "qual formato você quer sua particao root?(btrfs/ext4) " formato
while [[ "$formato" != "btrfs" && "$formato" != "ext4" ]]; do
    echo "Formato inválido. Por favor, escolha btrfs ou ext4."
    read -p "qual formato você quer sua particao root?(btrfs/ext4) " formato
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

set -o allexport
source ../respostas.env
set +o allexport

# Chamada para o playbook de particionamento
ansible-playbook main.yml --tags particionamento

chmod +x ./scripts/B-reflector.sh
bash ./scripts/B-reflector.sh
