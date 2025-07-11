#!/bin/bash
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
echo "recomendo usar 4 partições, uma pra root, uma pra home, uma pra swap e uma pra boot."
echo "boot deve ter 1G, root deve ter pelo menos 40G, swap deve ter ao menos 4G e home o resto."
echo "a partição de boot deve ter tipo EFI system, boot linux root(x86_64), home deve ter linux home e swap deve ter linux swap"
echo "Quando finalizar, pressione 'write' ou 'gravar' pra salvar suas alterações."
echo "---------------------------------------------------"
read -p "você entendeu tudo? (Y/n) " resposta
while [ "$resposta" != "Y" ] && [ "$resposta" != "y" ] && [ "$resposta" != "" ]; do
    echo "Por favor, leia as instruções novamente."
    read -p "você entendeu tudo? (Y/n) " resposta
done
echo "Continuando..."
sleep 1
lsblk
echo "---------------------------------------------------"
read -p "Digite o nome do disco a ser particionado (ex: sda ou nvme0n1): " disco
while [ ! -b "/dev/$disco" ]; do
    echo "Disco /dev/$disco não encontrado!"
    read -p "Digite o nome do disco a ser particionado (ex: sda ou nvme0n1): " disco
done
cfdisk "/dev/$disco"
echo "Particionamento concluído, você tem certeza de todas as partições? (caso as partições estejam corretas, digite 'Y', caso contrário, digite 'n')"
echo "caso elas estejam erradas, isso irá quebrar seu sistema."
read -p "Você tem certeza de todas as partições? (Y/n) " resposta
while [ "$resposta" != "Y" ] && [ "$resposta" != "y" ] && [ "$resposta" != "" ]; do
    echo "Por favor, verifique as partições novamente."
    cfdisk "/dev/$disco"
    fdisk -l "/dev/$disco"
    echo "Particionamento concluído, você tem certeza de todas as partições? (caso as partições estejam corretas, digite 'Y', caso contrário, digite 'n')"
    echo "Caso elas estejam erradas, isso irá quebrar seu sistema."
    read -p "Você tem certeza de todas as partições? (Y/n) " resposta
done
read -p "Na tua root, tu quer btrfs ou ext4? " formato
while [[ "$formato" != "btrfs" && "$formato" != "ext4" ]]; do
    echo "Formato inválido. Digite apenas 'btrfs' ou 'ext4'."
    read -p "Na tua root, tu quer btrfs ou ext4? " formato
done
lsblk
read -p "E qual tua partição de root? " root
read -p "E qual tua partição de swap? " swap
read -p "E qual tua partição de home? " home
read -p "E qual tua partição de boot? " boot
sleep 0.5
echo "... oooookay, pode deixar que daqui eu sigo"
echo "..."
tput bold; echo ">>> Formatando partições..."; tput sgr0
if [ "$formato" == "btrfs" ]; then
    mkfs.btrfs "/dev/$root"
else
    mkfs.ext4 "/dev/$root"
fi
mkswap "/dev/$swap"
mkfs.ext4 "/dev/$home"
mkfs.fat -F 32 "/dev/$boot"
fdisk -l
echo "---------------------------------------------------"
read -p "tudo certo?" r
while [ "$r" != "Y" ] && [ "$r" != "y" ] && [ "$r" != "" ]; do
    echo "Por favor, verifique as partições novamente e escreva os caminhos certos."
    fdisk -l
    read -p "qual tua partição de root? " root
    read -p "qual tua partição de swap? " swap
    read -p "qual tua partição de home? " home
    read -p "qual tua partição de boot? " boot
    if [ "$formato" == "btrfs" ]; then
        mkfs.btrfs "/dev/$root"
    else
        mkfs.ext4 "/dev/$root"
    fi
    mkswap "/dev/$swap"
    mkfs.ext4 "/dev/$home"
    mkfs.fat -F 32 "/dev/$boot"
    fdisk -l
    sleep 1
    echo "---------------------------------------------------"
    read -p "tudo certo?" r
done
mount "/dev/$root" /mnt
mkdir -p /mnt/{boot,home}
mount "/dev/$home" /mnt/home
mount "/dev/$boot" /mnt/boot
swapon "/dev/$swap"
sleep 1
echo "tudo finalizado e montado meu/minha/minhe rei/rainha/ra (sla como seria rei/rainha no gênero neutro)"
echo "partindo pro pacstrap..."
