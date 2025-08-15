#!/bin/bash
echo "$LANGC"
source scripts/resources.sh
if [ -f "$LANGC"==Portugues ]; then
  timedatectl
  loadkeys br-abnt2
  mkdir -p "tmp/.ansible-${USER}/tmp"
  if [ -d /sys/firmware/efi ]; then
    firmware="UEFI"
  else
    firmware="BIOS"
  fi
  echo "FIRMWARE=$firmware" >>./respostas.env

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
  set_env_var "ROOTP" "/dev/$root"
  set_env_var "HOMEP" "/dev/$home"
  set_env_var "BOOTP" "/dev/$boot"
  set_env_var "SWAPP" "/dev/$swap"

  echo ""
  echo "Partições salvas:"
  echo "ROOT=$root"
  echo "HOME=$home"
  echo "BOOT=$boot"
  echo "SWAP=$swap"
  echo "Disco principal: $disco"
  echo "Formato da partição root: $formato"
  echo "---------------------------------------------------"
  read -p "Confirma? (Y/n) " -r confirmacao
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
  source respostas.env
  set +a

  # Chamada para o playbook de particionamento
  ansible-playbook -vvv ./main.yaml --tags particionamento
elif [ -f "$LANGC"==English ]; then
  timedatectl
  loadkeys us
  mkdir -p "tmp/.ansible-${USER}/tmp"
  if [ -d /sys/firmware/efi ]; then
    firmware="UEFI"
  else
    firmware="BIOS"
  fi
  echo "FIRMWARE=$firmware" >>./respostas.env
  sleep 1
  echo "Preparing partitioning..."
  sleep 1
  echo "3..."
  sleep 1
  echo "2..."
  sleep 1
  echo "1..."
  echo "Hello? Is anyone there????? Alright, we're starting here, get ready to begin"
  echo ""
  echo "Let's start partitioning the disk"
  echo ""
  echo "we will use the cfdisk command, so make sure you are prepared."
  echo ""
  echo "I recommend using 4 partitions: root, home, swap, and boot."
  echo "boot = 1G with type EFI system | root = 40G+ / Linux root(x86_64) | swap = 4G+ / linux swap | home = remaining space / linux home"
  echo "Finalize with 'write' in cfdisk to apply the changes."
  echo "---------------------------------------------------"

  read -p "Did you understand everything (type N to confirm)? (y/N) " -r resposta
  while [[ "$resposta" == "Y" || "$resposta" == "y" || "$resposta" == "" ]]; do
    echo "Please, read the instructions again and STOP JUST HITTING ENTER!"
    read -p "Did you understand everything? (y/N) " -r resposta
  done
  echo "Continuing..."
  sleep 1

  echo "---------------------------------------------------"
  lsblk
  echo "---------------------------------------------------"

  read -p "Enter the disk to be partitioned (e.g., sda): " -r disco
  while [[ -z "$disco" || ! -b "/dev/$disco" ]]; do
    echo "Please, enter a valid disk."
    read -p "Enter the disk to be partitioned (e.g., sda): " -r disco
  done
  cfdisk "/dev/$disco"

  read -p "What is your ROOT partition? (e.g., sda2): " -r root
  while [[ -z "$root" || ! -b "/dev/$root" ]]; do
    echo "Please, enter a valid partition."
    read -p "What is your ROOT partition? (e.g., sda2): " -r root
  done

  read -p "What is your HOME partition? (e.g., sda4): " -r home
  while [[ -z "$home" || ! -b "/dev/$home" ]]; do
    echo "Please, enter a valid partition."
    read -p "What is your HOME partition? (e.g., sda4): " -r home
  done

  read -p "What is your BOOT partition? (e.g., sda1): " -r boot
  while [[ -z "$boot" || ! -b "/dev/$boot" ]]; do
    echo "Please, enter a valid partition."
    read -p "What is your BOOT partition? (e.g., sda1): " -r boot
  done

  read -p "What is your SWAP partition? (e.g., sda3): " -r swap
  while [[ -z "$swap" || ! -b "/dev/$swap" ]]; do
    echo "Please, enter a valid partition."
    read -p "What is your SWAP partition? (e.g., sda3): " -r swap
  done

  echo "The format of the root partition can be btrfs or ext4."
  echo "btrfs helps compress your root disk more, but worsens performance in games, for example, while ext4 is more traditional."
  read -p "What format do you want for your root partition? (btrfs/ext4) " -r formato

  while [[ "$formato" != "btrfs" && "$formato" != "ext4" ]]; do
    echo "Invalid format. Please choose btrfs or ext4."
    read -p "What format do you want for your root partition? (btrfs/ext4) " -r formato
  done

  set_env_var "FORMATO_ROOT" "$formato"
  set_env_var "ROOTP" "/dev/$root"
  set_env_var "HOMEP" "/dev/$home"
  set_env_var "BOOTP" "/dev/$boot"
  set_env_var "SWAPP" "/dev/$swap"

  echo ""
  echo "Partitions saved:"
  echo "ROOT=$root"
  echo "HOME=$home"
  echo "BOOT=$boot"
  echo "SWAP=$swap"
  echo "Main disk: $disco"
  echo "Format of the root partition: $formato"
  echo "---------------------------------------------------"

  read -p "Do you confirm? (Y/n) " -r confirmacao
  #while [[ "$confirmacao" != "Y" && "$confirmacao" != "y" && "$confirmacao" != "" ]]; do
  # echo "Please, confirm the partitions."
  # echo "ROOT=$root"
  # echo "HOME=$home"
  # echo "BOOT=$boot"
  # echo "SWAP=$swap"
  # echo "Main disk: $disco"
  # echo "Format of the root partition: $formato"
  # read -p "What is the current partition you want to change? (e.g., sda2): " particao_atual
  # read -p "To which one do you want to change? (sda2, sda1, etc): " mudanca
  # read -p "Confirm? (Y/n) " confirmacao
  # done

  set -a
  source respostas.env
  set +a

  # Call the partitioning playbook
  ansible-playbook -vvv ./main.yaml --tags particionamento
else
  echo "Language not recognized. Please set LANGC to either 'Portugues' or 'English'"
  bash scripts/A-particionamento.sh
fi
