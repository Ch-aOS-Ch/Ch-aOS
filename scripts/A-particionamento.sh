#!/bin/bash
set -a
source respostas.env
set +a
source scripts/resources.sh

# ==============================================================================
# SETUP DE IDIOMA E MENSAGENS
# Todas as strings visíveis para o usuário são definidas aqui.
# ==============================================================================
case "$LANGC" in
"Portugues")
  # Mensagens Gerais
  MSG_PREPARING="Preparando particionamento..."
  MSG_STARTING_PROMPT="Alô alô??? alguém aí????? beleza, tamo começando aqui, se prepara pra iniciar"
  MSG_LETS_PARTITION="Vamos começar a particionar o disco"
  MSG_CFDISK_INFO="vamos usar o comando cfdisk, então se certifique de se preparar."
  MSG_RECOMMENDATION="recomendo usar 4 partições: root, home, swap e boot."
  MSG_RECOMMENDATION_DETAILS="boot = 1G com tipo EFI system | root = 40G+ / Linux root(x86_64) | swap = 4G+ / linux swap | home = resto / linux home"
  MSG_FINALIZE="Finalize com 'write' ou 'gravar' no cfdisk pra aplicar as alterações."
  MSG_UNDERSTOOD_PROMPT="Você entendeu tudo (digite N para confirmar)? (y/N) "
  MSG_READ_AGAIN="Por favor, leia as instruções novamente e PARA DE FICAR SÓ DANDO ENTER!"
  MSG_CONTINUING="Continuando..."

  # Prompts de Entrada
  MSG_DISK_PROMPT="Digite o disco que vai ser particionado (ex: sda): "
  MSG_ROOT_PROMPT="qual a tua Partição ROOT? (ex: sda2): "
  MSG_HOME_PROMPT="qual a tua Partição HOME? (ex: sda4): "
  MSG_BOOT_PROMPT="qual a tua Partição BOOT? (ex: sda1): "
  MSG_SWAP_PROMPT="qual a tua Partição SWAP? (ex: sda3): "
  MSG_FORMAT_PROMPT="qual formato você quer sua particao root?(btrfs/ext4) "

  # Mensagens de Validação e Erro
  MSG_INVALID_DISK="Por favor, digite um disco válido."
  MSG_INVALID_PARTITION="Por favor, digite uma partição válida."
  MSG_INVALID_FORMAT="Formato inválido. Por favor, escolha btrfs ou ext4."

  # Loop de Confirmação
  MSG_CHECK_VALUES="Por favor, verifique os valores inseridos:"
  MSG_CONFIRM_PROMPT="As informações estão corretas? (Y/n) "
  MSG_CHANGE_PROMPT="Qual valor você deseja alterar? (ROOT, HOME, BOOT, SWAP, DISCO, FORMATO): "
  MSG_UPDATED_VALUES="Valores atualizados:"
  MSG_INVALID_OPTION="Opção inválida. Por favor, escolha uma das opções listadas."
  MSG_CONFIG_CONFIRMED="Ótimo! Configurações confirmadas."
  ;;
"English")
  # General Messages
  MSG_PREPARING="Preparing partitioning..."
  MSG_STARTING_PROMPT="Hello? Is anyone there????? Alright, we're starting here, get ready to begin"
  MSG_LETS_PARTITION="Let's start partitioning the disk"
  MSG_CFDISK_INFO="we will use the cfdisk command, so make sure you are prepared."
  MSG_RECOMMENDATION="I recommend using 4 partitions: root, home, swap, and boot."
  MSG_RECOMMENDATION_DETAILS="boot = 1G with type EFI system | root = 40G+ / Linux root(x86_64) | swap = 4G+ / linux swap | home = remaining space / linux home"
  MSG_FINALIZE="Finalize with 'write' in cfdisk to apply the changes."
  MSG_UNDERSTOOD_PROMPT="Did you understand everything (type N to confirm)? (y/N) "
  MSG_READ_AGAIN="Please, read the instructions again and STOP JUST HITTING ENTER!"
  MSG_CONTINUING="Continuing..."

  # Input Prompts
  MSG_DISK_PROMPT="Enter the disk to be partitioned (e.g., sda): "
  MSG_ROOT_PROMPT="What is your ROOT partition? (e.g., sda2): "
  MSG_HOME_PROMPT="What is your HOME partition? (e.g., sda4): "
  MSG_BOOT_PROMPT="What is your BOOT partition? (e.g., sda1): "
  MSG_SWAP_PROMPT="What is your SWAP partition? (e.g., sda3): "
  MSG_FORMAT_PROMPT="What format do you want for your root partition? (btrfs/ext4) "

  # Validation and Error Messages
  MSG_INVALID_DISK="Please, enter a valid disk."
  MSG_INVALID_PARTITION="Please, enter a valid partition."
  MSG_INVALID_FORMAT="Invalid format. Please choose btrfs or ext4."

  # Confirmation Loop
  MSG_CHECK_VALUES="Please verify the entered values:"
  MSG_CONFIRM_PROMPT="Are the details correct? (Y/n) "
  MSG_CHANGE_PROMPT="Which value do you want to change? (ROOT, HOME, BOOT, SWAP, DISK, FORMAT): "
  MSG_UPDATED_VALUES="Updated values:"
  MSG_INVALID_OPTION="Invalid option. Please choose one of the listed options."
  MSG_CONFIG_CONFIRMED="Great! Settings confirmed."
  ;;
*)
  echo "Language not recognized. Please set LANGC to either 'Portugues' or 'English'"
  exit 1
  ;;
esac

# ==============================================================================
# FUNÇÕES HELPERS
# ==============================================================================

# Função para pedir e validar uma partição.
# Argumento $1: A mensagem de prompt a ser exibida.
prompt_for_partition() {
  local prompt_message="$1"
  local partition_var

  read -p "$prompt_message" -r partition_var
  while [[ -z "$partition_var" || ! -b "/dev/$partition_var" ]]; do
    echo "$MSG_INVALID_PARTITION"
    read -p "$prompt_message" -r partition_var
  done

  echo "$partition_var"
}

# ==============================================================================
# FLUXO PRINCIPAL DO SCRIPT
# ==============================================================================

# Configuração inicial do sistema
if [ "$LANGC" = "Portugues" ]; then
  loadkeys br-abnt2
else
  loadkeys us
fi
timedatectl

# Preparação e instruções
if [ -d /sys/firmware/efi ]; then
  firmware="UEFI"
else
  firmware="BIOS"
fi

echo "$MSG_PREPARING"
sleep 1
echo "3..."
sleep 1
echo "2..."
sleep 1
echo "1..."

echo "$MSG_STARTING_PROMPT"
echo ""
echo "$MSG_LETS_PARTITION"
echo "$MSG_CFDISK_INFO"
echo ""
echo "$MSG_RECOMMENDATION"
echo "$MSG_RECOMMENDATION_DETAILS"
echo "$MSG_FINALIZE"
echo "---------------------------------------------------"

read -p "$MSG_UNDERSTOOD_PROMPT" -r resposta
while [[ "$resposta" == "Y" || "$resposta" == "y" || "$resposta" == "" ]]; do
  echo "$MSG_READ_AGAIN"
  read -p "$MSG_UNDERSTOOD_PROMPT" -r resposta
done

echo "$MSG_CONTINUING"
sleep 1

# Seleção do disco e particionamento
echo "---------------------------------------------------"
lsblk
echo "---------------------------------------------------"

read -p "$MSG_DISK_PROMPT" -r disco
while [[ -z "$disco" || ! -b "/dev/$disco" ]]; do
  echo "$MSG_INVALID_DISK"
  read -p "$MSG_DISK_PROMPT" -r disco
done

cfdisk "/dev/$disco"

# Coleta das informações de partição
root=$(prompt_for_partition "$MSG_ROOT_PROMPT")
home=$(prompt_for_partition "$MSG_HOME_PROMPT")
boot=$(prompt_for_partition "$MSG_BOOT_PROMPT")
swap=$(prompt_for_partition "$MSG_SWAP_PROMPT")

read -p "$MSG_FORMAT_PROMPT" -r formato
while [[ "$formato" != "btrfs" && "$formato" != "ext4" ]]; do
  echo "$MSG_INVALID_FORMAT"
  read -p "$MSG_FORMAT_PROMPT" -r formato
done

# Loop de verificação e correção
confirmacao="n" # Força a entrada no loop na primeira vez
while ! [[ "$confirmacao" == "Y" || "$confirmacao" == "y" || "$confirmacao" == "" ]]; do
  # Exibe o resumo
  echo ""
  echo "---------------------------------------------------"
  echo "$MSG_CHECK_VALUES"
  echo "  [ROOT]    => /dev/$root"
  echo "  [HOME]    => /dev/$home"
  echo "  [BOOT]    => /dev/$boot"
  echo "  [SWAP]    => /dev/$swap"
  echo "  [DISCO]   => /dev/$disco"
  echo "  [FORMATO] => $formato"
  echo "  [FIRMWARE]=> $firmware"
  echo "---------------------------------------------------"

  read -p "$MSG_CONFIRM_PROMPT" -r confirmacao

  # Se a confirmação não for positiva, entra no modo de alteração
  if ! [[ "$confirmacao" == "Y" || "$confirmacao" == "y" || "$confirmacao" == "" ]]; then
    read -p "$MSG_CHANGE_PROMPT" -r var_to_change
    case $var_to_change in
    ROOT | root) root=$(prompt_for_partition "$MSG_ROOT_PROMPT") ;;
    HOME | home) home=$(prompt_for_partition "$MSG_HOME_PROMPT") ;;
    BOOT | boot) boot=$(prompt_for_partition "$MSG_BOOT_PROMPT") ;;
    SWAP | swap) swap=$(prompt_for_partition "$MSG_SWAP_PROMPT") ;;
    DISCO | disco)
      read -p "$MSG_DISK_PROMPT" -r disco
      while [[ -z "$disco" || ! -b "/dev/$disco" ]]; do
        echo "$MSG_INVALID_DISK"
        read -p "$MSG_DISK_PROMPT" -r disco
      done
      ;;
    FORMATO | formato)
      read -p "$MSG_FORMAT_PROMPT" -r formato
      while [[ "$formato" != "btrfs" && "$formato" != "ext4" ]]; do
        echo "$MSG_INVALID_FORMAT"
        read -p "$MSG_FORMAT_PROMPT" -r formato
      done
      ;;
    *) echo "$MSG_INVALID_OPTION" ;;
    esac
  fi
done

echo "$MSG_CONFIG_CONFIRMED"

# Salva as variáveis finais no arquivo de respostas
set_env_var "DISCO" "$disco"
set_env_var "ROOTP" "/dev/$root"
set_env_var "HOMEP" "/dev/$home"
set_env_var "BOOTP" "/dev/$boot"
set_env_var "SWAPP" "/dev/$swap"
set_env_var "FORMATO_ROOT" "$formato"
set_env_var "FIRMWARE" "$firmware"

# Chamada para o playbook Ansible
set -a
source respostas.env
set +a
ansible-playbook -vvv ./main.yaml --tags particionamento
