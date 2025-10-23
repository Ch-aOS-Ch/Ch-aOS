#!/bin/bash
set -e
set -a
source respostas.env
set +a
source scripts/resources.sh
plugin_dir="./plugins/"

# ==============================================================================
# SETUP DE IDIOMA E MENSAGENS
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
  MSG_ROOT_PROMPT="Qual a tua Partição ROOT? (ex: sda2): "
  MSG_ROOT_LABEL_PROMPT="Qual a LABEL para a partição ROOT? (ex: ARCH_ROOT): "
  MSG_HOME_PROMPT="Qual a tua Partição HOME? (ex: sda4): "
  MSG_HOME_LABEL_PROMPT="Qual a LABEL para a partição HOME? (ex: ARCH_HOME): "
  MSG_BOOT_PROMPT="Qual a tua Partição BOOT? (ex: sda1): "
  MSG_BOOT_LABEL_PROMPT="Qual a LABEL para a partição BOOT? (ex: ESP): "
  MSG_SWAP_PROMPT="Qual a tua Partição SWAP? (ex: sda3): "
  MSG_SWAP_LABEL_PROMPT="Qual a LABEL para a partição SWAP? (ex: SWAP): "
  MSG_FORMAT_PROMPT="Qual formato você quer sua particao root?(btrfs/ext4) "
  MSG_BOOTLOADER_PROMPT="Qual bootloader você deseja usar? (grub/refind): "

  # Mensagens de Validação e Erro
  MSG_INVALID_DISK="Por favor, digite um disco válido."
  MSG_INVALID_PARTITION="Por favor, digite uma partição válida."
  MSG_INVALID_FORMAT="Formato inválido. Por favor, escolha btrfs ou ext4."
  MSG_INVALID_LABEL="Label inválido. Use apenas letras e números, no máximo 16 caracteres."
  MSG_INVALID_BOOTLOADER="Bootloader inválido. Escolha grub ou refind."

  # Loop de Confirmação
  MSG_CHECK_VALUES="Por favor, verifique os valores inseridos:"
  MSG_CONFIRM_PROMPT="As informações estão corretas? (Y/n) "
  MSG_CHANGE_PROMPT="Qual valor você deseja alterar? (ROOT, HOME, BOOT, SWAP, DISCO, FORMATO, BOOTLOADER): "
  MSG_CONFIG_CONFIRMED="Ótimo! Configurações confirmadas."

  # Mensagens específicas da lógica de plugin
  MSG_EXISTING_PLUGINS_FOUND="Plugins existentes foram encontrados:"
  MSG_CHOICE_PROMPT="Deseja criar um NOVO plugin ou usar um EXISTENTE? (novo/usar): "
  MSG_PROMPT_WHICH_PLUGIN="Digite o nome do plugin que você quer usar (ex: custom1.yml): "
  MSG_INVALID_FILE="Arquivo inválido ou não encontrado. Por favor, escolha um da lista."
  MSG_USING_EXISTING="Usando o plugin existente:"
  MSG_CREATING_NEW="Criando novo plugin:"
  MSG_WANT_HOME_PARTITION="Você deseja criar uma partição HOME? (S/n) "
  MSG_WANT_SWAP_PARTITION="Você deseja criar uma partição SWAP? (S/n) "
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
  MSG_ROOT_LABEL_PROMPT="What is the LABEL for the ROOT partition? (e.g., ARCH_ROOT): "
  MSG_HOME_PROMPT="What is your HOME partition? (e.g., sda4): "
  MSG_HOME_LABEL_PROMPT="What is the LABEL for the HOME partition? (e.g., ARCH_HOME): "
  MSG_BOOT_PROMPT="What is your BOOT partition? (e.g., sda1): "
  MSG_BOOT_LABEL_PROMPT="What is the LABEL for the BOOT partition? (e.g., ESP): "
  MSG_SWAP_PROMPT="What is your SWAP partition? (e.g., sda3): "
  MSG_SWAP_LABEL_PROMPT="What is the LABEL for the SWAP partition? (e.g., SWAP): "
  MSG_FORMAT_PROMPT="What format do you want for your root partition? (btrfs/ext4) "
  MSG_BOOTLOADER_PROMPT="Which bootloader do you want to use? (grub/refind): "

  # Validation and Error Messages
  MSG_INVALID_DISK="Please, enter a valid disk."
  MSG_INVALID_PARTITION="Please, enter a valid partition."
  MSG_INVALID_FORMAT="Invalid format. Please choose btrfs or ext4."
  MSG_INVALID_LABEL="Invalid label. Use only letters and numbers, max 16 characters."
  MSG_INVALID_BOOTLOADER="Invalid bootloader. Choose grub or refind."

  # Confirmation Loop
  MSG_CHECK_VALUES="Please verify the entered values:"
  MSG_CONFIRM_PROMPT="Are the details correct? (Y/n) "
  MSG_CHANGE_PROMPT="Which value do you want to change? (ROOT, HOME, BOOT, SWAP, DISK, FORMAT, BOOTLOADER): "
  MSG_CONFIG_CONFIRMED="Great! Settings confirmed."

  # Plugin-specific logic messages
  MSG_EXISTING_PLUGINS_FOUND="Existing plugins were found:"
  MSG_CHOICE_PROMPT="Do you want to create a NEW plugin or USE an existing one? (new/use): "
  MSG_PROMPT_WHICH_PLUGIN="Enter the name of the plugin you want to use (e.g., custom1.yml): "
  MSG_INVALID_FILE="Invalid file or not found. Please choose one from the list."
  MSG_USING_EXISTING="Using existing plugin:"
  MSG_CREATING_NEW="Creating new plugin:"
  MSG_WANT_HOME_PARTITION="Do you want to create a HOME partition? (Y/n) "
  MSG_WANT_SWAP_PARTITION="Do you want to create a SWAP partition? (Y/n) "
  ;;
*)
  echo "Language not recognized. Please set LANGC to either 'Portugues' or 'English'"
  exit 1
  ;;
esac

# ==============================================================================
# FUNÇÕES HELPERS
# ==============================================================================

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

prompt_for_label() {
  local prompt_message="$1"
  local label_var
  read -p "$prompt_message" -r label_var
  while [[ ! "$label_var" =~ ^[a-zA-Z0-9_]{1,16}$ ]]; do
      echo "$MSG_INVALID_LABEL"
      read -p "$prompt_message" -r label_var
  done
  echo "$label_var"
}

select_or_create_plugin_file() {
  shopt -s nullglob
  mkdir -p "$plugin_dir"
  local existing_plugins=("$plugin_dir"custom*.yml)
  local choice arquivo
  if [ ${#existing_plugins[@]} -gt 0 ]; then
    echo "$MSG_EXISTING_PLUGINS_FOUND" >&2
    for file in "${existing_plugins[@]}"; do basename "$file"; done >&2
    echo "" >&2
    read -rp "$MSG_CHOICE_PROMPT" choice
  else
    choice="novo"
  fi
  shopt -u nullglob
  choice=$(echo "$choice" | tr '[:upper:]' '[:lower:]')
  if [[ "$choice" == "usar" || "$choice" == "use" ]]; then
    read -rp "$MSG_PROMPT_WHICH_PLUGIN" arquivo
    while [[ -z "$arquivo" || ! -f "$plugin_dir$arquivo" ]]; do
      echo "$MSG_INVALID_FILE" >&2
      for file in "${existing_plugins[@]}"; do basename "$file"; done >&2
      read -rp "$MSG_PROMPT_WHICH_PLUGIN" arquivo
    done
    echo "$MSG_USING_EXISTING $arquivo" >&2
    set_env_var "PLUGIN" "$arquivo"
  else
    local qtd
    qtd=$(find "$plugin_dir" -maxdepth 1 -type f -name 'custom*.yml' | wc -l)
    arquivo="custom$((qtd + 1)).yml"
    echo "{}" >"$plugin_dir$arquivo"
    echo "$MSG_CREATING_NEW $arquivo" >&2
    set_env_var "PLUGIN_PATH" "$HOME/Ch-aronte/$plugin_dir$arquivo"
    set_env_var "CHOICE" "$choice"
  fi
  echo "$arquivo"
}

# ==============================================================================
# FLUXO PRINCIPAL DO SCRIPT
# ==============================================================================

set -a; source respostas.env; set +a

if [ "$LANGC" = "Portugues" ]; then loadkeys br-abnt2; else loadkeys us; fi
timedatectl

arquivo_plugin=$(select_or_create_plugin_file)
set_env_var "PLUGIN" "$arquivo_plugin"

if [ -d /sys/firmware/efi ]; then
  yq -iy '.firmware = "UEFI"' "plugins/$PLUGIN"
  set_env_var "FIRMWARE" "UEFI"
  firmware="UEFI"
else
  yq -iy '.firmware = "BIOS"' "plugins/$PLUGIN"
  set_env_var "FIRMWARE" "BIOS"
  firmware="BIOS"
fi

echo "$MSG_PREPARING"; sleep 1; echo "3..."; sleep 1; echo "2..."; sleep 1; echo "1..."
echo "$MSG_STARTING_PROMPT"; echo ""; echo "$MSG_LETS_PARTITION"; echo "$MSG_CFDISK_INFO"; echo ""
echo "$MSG_RECOMMENDATION"; echo "$MSG_RECOMMENDATION_DETAILS"; echo "$MSG_FINALIZE"
echo "---------------------------------------------------"

read -p "$MSG_UNDERSTOOD_PROMPT" -r resposta
while [[ "$resposta" == "Y" || "$resposta" == "y" || "$resposta" == "" ]]; do
  echo "$MSG_READ_AGAIN"
  read -p "$MSG_UNDERSTOOD_PROMPT" -r resposta
done

echo "$MSG_CONTINUING"; sleep 1
echo "---------------------------------------------------"; lsblk; echo "---------------------------------------------------"

read -p "$MSG_DISK_PROMPT" -r disco
while [[ -z "$disco" || ! -b "/dev/$disco" ]]; do
  echo "$MSG_INVALID_DISK"; read -p "$MSG_DISK_PROMPT" -r disco
done

cfdisk "/dev/$disco"

# Coleta das informações de partição
root_dev=$(prompt_for_partition "$MSG_ROOT_PROMPT")
root_label=$(prompt_for_label "$MSG_ROOT_LABEL_PROMPT")
boot_dev=$(prompt_for_partition "$MSG_BOOT_PROMPT")
boot_label=$(prompt_for_label "$MSG_BOOT_LABEL_PROMPT")

read -rp "$MSG_WANT_HOME_PARTITION" want_home
if [[ "$want_home" == "Y" || "$want_home" == "y" || "$want_home" == "" ]]; then
  home_dev=$(prompt_for_partition "$MSG_HOME_PROMPT")
  home_label=$(prompt_for_label "$MSG_HOME_LABEL_PROMPT")
else
  home_dev=""; home_label=""
fi

read -rp "$MSG_WANT_SWAP_PARTITION" want_swap
if [[ "$want_swap" == "Y" || "$want_swap" == "y" || "$want_swap" == "" ]]; then
  swap_dev=$(prompt_for_partition "$MSG_SWAP_PROMPT")
  swap_label=$(prompt_for_label "$MSG_SWAP_LABEL_PROMPT")
else
  swap_dev=""; swap_label=""
fi

read -p "$MSG_FORMAT_PROMPT" -r formato
while [[ "$formato" != "btrfs" && "$formato" != "ext4" ]]; do
  echo "$MSG_INVALID_FORMAT"; read -p "$MSG_FORMAT_PROMPT" -r formato
done

read -p "$MSG_BOOTLOADER_PROMPT" -r bootloader
while [[ "$bootloader" != "grub" && "$bootloader" != "refind" ]]; do
    echo "$MSG_INVALID_BOOTLOADER"; read -p "$MSG_BOOTLOADER_PROMPT" -r bootloader
done

# Loop de verificação e correção
confirmacao="n"
while ! [[ "$confirmacao" == "Y" || "$confirmacao" == "y" || "$confirmacao" == "" ]]; do
  echo ""; echo "---------------------------------------------------"
  echo "$MSG_CHECK_VALUES"
  echo "  [DISCO]      => /dev/$disco"
  echo "  [ROOT]       => Device: /dev/$root_dev, Label: $root_label"
  echo "  [HOME]       => Device: /dev/$home_dev, Label: $home_label"
  echo "  [BOOT]       => Device: /dev/$boot_dev, Label: $boot_label"
  echo "  [SWAP]       => Device: /dev/$swap_dev, Label: $swap_label"
  echo "  [FORMATO]    => $formato"
  echo "  [FIRMWARE]   => $firmware"
  echo "  [BOOTLOADER] => $bootloader"
  echo "---------------------------------------------------"

  read -p "$MSG_CONFIRM_PROMPT" -r confirmacao

  if ! [[ "$confirmacao" == "Y" || "$confirmacao" == "y" || "$confirmacao" == "" ]]; then
    read -p "$MSG_CHANGE_PROMPT" -r var_to_change
    case $(echo "$var_to_change" | tr '[:upper:]' '[:lower:]') in
    root) root_dev=$(prompt_for_partition "$MSG_ROOT_PROMPT"); root_label=$(prompt_for_label "$MSG_ROOT_LABEL_PROMPT") ;;
    home) home_dev=$(prompt_for_partition "$MSG_HOME_PROMPT"); home_label=$(prompt_for_label "$MSG_HOME_LABEL_PROMPT") ;;
    boot) boot_dev=$(prompt_for_partition "$MSG_BOOT_PROMPT"); boot_label=$(prompt_for_label "$MSG_BOOT_LABEL_PROMPT") ;;
    swap) swap_dev=$(prompt_for_partition "$MSG_SWAP_PROMPT"); swap_label=$(prompt_for_label "$MSG_SWAP_LABEL_PROMPT") ;;
    disco) read -p "$MSG_DISK_PROMPT" -r disco; while [[ -z "$disco" || ! -b "/dev/$disco" ]]; do echo "$MSG_INVALID_DISK"; read -p "$MSG_DISK_PROMPT" -r disco; done ;;
    formato) read -p "$MSG_FORMAT_PROMPT" -r formato; while [[ "$formato" != "btrfs" && "$formato" != "ext4" ]]; do echo "$MSG_INVALID_FORMAT"; read -p "$MSG_FORMAT_PROMPT" -r formato; done ;;
    bootloader) read -p "$MSG_BOOTLOADER_PROMPT" -r bootloader; while [[ "$bootloader" != "grub" && "$bootloader" != "refind" ]]; do echo "$MSG_INVALID_BOOTLOADER"; read -p "$MSG_BOOTLOADER_PROMPT" -r bootloader; done ;;
    *) echo "$MSG_INVALID_OPTION" ;;
    esac
  fi
done

echo "$MSG_CONFIG_CONFIRMED"

# Salva tudo no plugin YAML
yq -iy ".particoes.root.device = \"/dev/$root_dev\"" "plugins/$PLUGIN"
yq -iy ".particoes.root.label = \"$root_label\"" "plugins/$PLUGIN"
yq -iy ".particoes.root.formato = \"$formato\"" "plugins/$PLUGIN"

yq -iy ".particoes.home.device = \"/dev/$home_dev\"" "plugins/$PLUGIN"
yq -iy ".particoes.home.label = \"$home_label\"" "plugins/$PLUGIN"

yq -iy ".particoes.boot.device = \"/dev/$boot_dev\"" "plugins/$PLUGIN"
yq -iy ".particoes.boot.label = \"$boot_label\"" "plugins/$PLUGIN"


yq -iy ".particoes.swap.device = \"/dev/$swap_dev\"" "plugins/$PLUGIN"
yq -iy ".particoes.swap.label = \"$swap_label\"" "plugins/$PLUGIN"

yq -iy ".bootloader = \"$bootloader\"" "plugins/$PLUGIN"

# Salva variáveis de ambiente para scripts subsequentes, se necessário
set_env_var "DISCO" "$disco"

ansible-playbook -vvv ./main.yaml --tags particionamento -e @plugins/"$PLUGIN"
