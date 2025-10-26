#!/bin/bash

# ==============================================================================
# SETUP DE IDIOMA E MENSAGENS
# ==============================================================================
case "$LANGC" in
"Portugues")
  # A-particionamento.sh
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
  MSG_INVALID_DISK="Por favor, digite um disco válido."
  MSG_INVALID_PARTITION="Por favor, digite uma partição válida."
  MSG_INVALID_FORMAT="Formato inválido. Por favor, escolha btrfs ou ext4."
  MSG_INVALID_LABEL="Label inválido. Use apenas letras e números, no máximo 16 caracteres."
  MSG_INVALID_BOOTLOADER="Bootloader inválido. Escolha grub ou refind."
  MSG_INVALID_BOOTLOADER_BIOS="Refind não é compatível com BIOS."
  MSG_CHECK_VALUES="Por favor, verifique os valores inseridos:"
  MSG_CONFIRM_PROMPT="As informações estão corretas? (Y/n) "
  MSG_CHANGE_PROMPT="Qual valor você deseja alterar? (ROOT, HOME, BOOT, SWAP, DISCO, FORMATO, BOOTLOADER): "
  MSG_CONFIG_CONFIRMED="Ótimo! Configurações confirmadas."
  MSG_EXISTING_PLUGINS_FOUND="Ch-obolos existentes foram encontrados:"
  MSG_CHOICE_PROMPT="Deseja criar um NOVO plugin ou usar um EXISTENTE? (novo/usar): "
  MSG_PROMPT_WHICH_PLUGIN="Digite o nome do plugin que você quer usar (ex: custom1.yml): "
  MSG_INVALID_FILE="Arquivo inválido ou não encontrado. Por favor, escolha um da lista."
  MSG_USING_EXISTING="Usando o plugin existente:"
  MSG_CREATING_NEW="Criando novo plugin:"
  MSG_WANT_HOME_PARTITION="Você deseja criar uma partição HOME? (S/n) "
  MSG_WANT_SWAP_PARTITION="Você deseja criar uma partição SWAP? (S/n) "
  MSG_SEPARATOR="---------------------------------------------------"
  MSG_CONFIGURING_BOOT_PARTITION="--- Configurando partição BOOT (Obrigatória) ---"
  MSG_PROMPT_BOOT_PART_NUMBER="Número da partição para BOOT (ex: 1): "
  MSG_PROMPT_BOOT_PART_SIZE="Tamanho da partição BOOT (ex: 1GB): "
  MSG_PROMPT_BOOT_PART_LABEL="Nome/Label para BOOT (ex: ESP): "
  MSG_CONFIGURING_ROOT_PARTITION="--- Configurando partição ROOT (Obrigatória) ---"
  MSG_PROMPT_ROOT_PART_NUMBER="Número da partição para ROOT (ex: 2): "
  MSG_PROMPT_ROOT_PART_SIZE="Tamanho da partição ROOT (ex: 50GB, 100% para usar o resto): "
  MSG_PROMPT_ROOT_PART_LABEL="Nome/Label para ROOT (ex: ARCH_ROOT): "
  MSG_PROMPT_ROOT_PART_FORMAT="Formato para ROOT (ext4/btrfs): "
  MSG_CONFIGURING_HOME_PARTITION="--- Configurando partição HOME ---"
  MSG_PROMPT_HOME_PART_NUMBER="Número da partição para HOME (ex: 3): "
  MSG_PROMPT_HOME_PART_SIZE="Tamanho da partição HOME (ex: 100% para usar o resto): "
  MSG_PROMPT_HOME_PART_LABEL="Nome/Label para HOME (ex: ARCH_HOME): "
  MSG_CONFIGURING_SWAP_PARTITION="--- Configurando partição SWAP ---"
  MSG_PROMPT_SWAP_PART_NUMBER="Número da partição para SWAP (ex: 4): "
  MSG_PROMPT_SWAP_PART_SIZE="Tamanho da partição SWAP (ex: 8GB): "
  MSG_PROMPT_SWAP_PART_LABEL="Nome/Label para SWAP (ex: SWAP): "
  MSG_GENERATED_PARTITION_CONFIG="Configuração de partição gerada:"
  MSG_ANSIBLE_APPLYING_CHANGES="Executando Ansible para aplicar as mudanças..."
  MSG_PROMPT_RUN_AGAIN_PARTITION="Particionamento já foi feito. Deseja executar novamente? (s/N) "
  MSG_PROMPT_RUN_AGAIN_REFLECTOR="Reflector já foi executado. Deseja executar novamente? (s/N) "
  MSG_PROMPT_RUN_AGAIN_INSTALL="Instalação base já foi feita. Deseja executar novamente? (s/N) "

  # B-reflector.sh
  MSG_ALMOST_FORGOT="Opa, quase que eu me esqueci de rodar o reflector, pera ae, vai ser 2 tempo"
  MSG_TYPING_SOUNDS="[sons de teclado]"
  MSG_INSTALLING="Ai ai... não temos o reflector, deixa que eu instalo rapidão"
  MSG_COMMAND_IS="jesus amado, que comando grande... aliás, é esse aqui:"
  FINALIZESC="Prontin, tá no grau."

  # C-instalacao.sh
  MSG_CONTINUE="Beleza, mirrors atualizados. Bora continuar..."
  MSG_SHOW_PKGS="Ok, agora vou te mostrar os pacotes essenciais..."
  MSG_WANT_MORE="Quer mais algum pacote? (Y/n) "
  MSG_PKG_NAME="Digite o nome do pacote: "
  MSG_NOT_FOUND="Pacote não encontrado."
  MSG_ADDING="Adicionando"
  MSG_ALREADY_SELECTED="Pacote já selecionado ou já presente no arquivo."
  MSG_ANY_MORE="Mais algum? (Y/n) "
  MSG_WHICH_REPO="Qual repositório você quer usar? (extra, multilib, cachy) "
  MSG_TRY_AGAIN="Tente novamente: "

  # D-regiao.sh
  MSG_START="Ok, vamos configurar a região e o idioma do seu sistema."
  MSG_TIMEZONE_INFO="Primeiro, o fuso horário. Você pode ver uma lista com 'timedatectl list-timezones'."
  MSG_TIMEZONE_PROMPT="Digite o seu fuso horário (ex: America/Sao_Paulo): "
  DEFAULT_REGION="America/Sao_Paulo"
  MSG_INVALID_REGION="Fuso horário inválido! O arquivo para essa região não existe em /usr/share/zoneinfo/. Tente novamente."
  MSG_LOCALE_INFO="Agora, vamos configurar o idioma (locale) e o layout do teclado (keymap)."
  MSG_LOCALE_PROMPT="Digite o seu locale principal (ex: pt_BR): "
  DEFAULT_LOCALE="pt_BR"
  MSG_ADD_ANOTHER_LOCALE="Deseja adicionar outro locale para ser gerado pelo sistema? (S/n) "
  MSG_NEXT_LOCALE_PROMPT="Digite o próximo locale (ex: en_US): "
  MSG_KEYMAP_PROMPT="Digite o layout do seu teclado (ex: br-abnt2): "
  DEFAULT_KEYMAP="br-abnt2"
  MSG_CONFIG_SAVED="Configurações de região salvas no seu plugin."

  # E-personalizacao.sh
  MSG_HOSTNAME_PROMPT="ok, me dá um nome pro seu pc aí... e pelo amor de deus, me dá um nome bonito... "
  MSG_INVALID_HOSTNAME="Nome inválido. Só letras, números, ponto ou hífen. Tenta de novo aí oh jegue: "
  MSG_RUNNING_MKINITCPIO="rodando mkinitcpio -P..."
  MSG_MKINITCPIO_DONE="aí sim porra, rodou. Agora vamo settar tua senha de root (sem 1234 seu jegue)"
  MSG_SET_USER="agora me fala teu user, vamo criar e tacar ele lá no sudoers"
  MSG_USERNAME_PROMPT="Nome do teu usuário: "
  MSG_INVALID_USERNAME="Nome de usuário inválido. Deve começar com letra minúscula e conter apenas letras minúsculas, números, _ ou -. Mals aí "
  MSG_WANT_DOTS="Você tem alguma dotfile ou nem? (S/n)"

  # F-bootloader.sh
  MSG_START_BOOTLOADER="belezinha belezinha, agora é a parte final, tá preparado?"
  MSG_CONFIGURING="Configurando o bootloader via Ansible..."
  MSG_ENABLE_NETWORK="Habilitando o NetworkManager para iniciar com o sistema..."
  MSG_GOODBYE_1="Ok, meu trabalho aqui tá feito, agora é contigo. Em teoria, é só reiniciar."
  MSG_GOODBYE_2="Se der ruim, a culpa não é minha! Brincadeira, tentei fazer o script redondinho."
  MSG_GOODBYE_3="Se encontrar um bug, abra uma issue no GitHub. Obrigado por usar o Ch-aronte!"

  # G-dotfiles.sh
  MSG_LOADING_DOTS="Fecho, carregando suas dots."
  ;;
"English")
  # A-particionamento.sh
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
  MSG_INVALID_DISK="Please, enter a valid disk."
  MSG_INVALID_PARTITION="Please, enter a valid partition."
  MSG_INVALID_FORMAT="Invalid format. Please choose btrfs or ext4."
  MSG_INVALID_LABEL="Invalid label. Use only letters and numbers, max 16 characters."
  MSG_INVALID_BOOTLOADER="Invalid bootloader. Choose grub or refind."
  MSG_INVALID_BOOTLOADER_BIOS="Refind is not compatible with BIOS."
  MSG_CHECK_VALUES="Please verify the entered values:"
  MSG_CONFIRM_PROMPT="Are the details correct? (Y/n) "
  MSG_CHANGE_PROMPT="Which value do you want to change? (ROOT, HOME, BOOT, SWAP, DISK, FORMAT, BOOTLOADER): "
  MSG_CONFIG_CONFIRMED="Great! Settings confirmed."
  MSG_EXISTING_PLUGINS_FOUND="Existing Ch-obolos were found:"
  MSG_CHOICE_PROMPT="Do you want to create a NEW plugin or USE an existing one? (new/use): "
  MSG_PROMPT_WHICH_PLUGIN="Enter the name of the plugin you want to use (e.g., custom1.yml): "
  MSG_INVALID_FILE="Invalid file or not found. Please choose one from the list."
  MSG_USING_EXISTING="Using existing plugin:"
  MSG_CREATING_NEW="Creating new plugin:"
  MSG_WANT_HOME_PARTITION="Do you want to create a HOME partition? (Y/n) "
  MSG_WANT_SWAP_PARTITION="Do you want to create a SWAP partition? (Y/n) "
  MSG_SEPARATOR="---------------------------------------------------"
  MSG_CONFIGURING_BOOT_PARTITION="--- Configuring BOOT partition (Required) ---"
  MSG_PROMPT_BOOT_PART_NUMBER="Partition number for BOOT (e.g., 1): "
  MSG_PROMPT_BOOT_PART_SIZE="Partition size for BOOT (e.g., 1GB): "
  MSG_PROMPT_BOOT_PART_LABEL="Name/Label for BOOT (e.g., ESP): "
  MSG_CONFIGURING_ROOT_PARTITION="--- Configuring ROOT partition (Required) ---"
  MSG_PROMPT_ROOT_PART_NUMBER="Partition number for ROOT (e.g., 2): "
  MSG_PROMPT_ROOT_PART_SIZE="Partition size for ROOT (e.g., 50GB, 100% for the rest of the disk): "
  MSG_PROMPT_ROOT_PART_LABEL="Name/Label for ROOT (e.g., ARCH_ROOT): "
  MSG_PROMPT_ROOT_PART_FORMAT="Format for ROOT (ext4/btrfs): "
  MSG_CONFIGURING_HOME_PARTITION="--- Configuring HOME partition ---"
  MSG_PROMPT_HOME_PART_NUMBER="Partition number for HOME (e.g., 3): "
  MSG_PROMPT_HOME_PART_SIZE="Partition size for HOME (e.g., 100% to use the rest): "
  MSG_PROMPT_HOME_PART_LABEL="Name/Label for HOME (e.g., ARCH_HOME): "
  MSG_CONFIGURING_SWAP_PARTITION="--- Configuring SWAP partition ---"
  MSG_PROMPT_SWAP_PART_NUMBER="Partition number for SWAP (e.g., 4): "
  MSG_PROMPT_SWAP_PART_SIZE="Partition size for SWAP (e.g., 8GB): "
  MSG_PROMPT_SWAP_PART_LABEL="Name/Label for SWAP (e.g., SWAP): "
  MSG_GENERATED_PARTITION_CONFIG="Generated partition configuration:"
  MSG_ANSIBLE_APPLYING_CHANGES="Executing Ansible to apply changes..."
  MSG_PROMPT_RUN_AGAIN_PARTITION="Partitioning is already done. Do you want to run it again? (y/N) "
  MSG_PROMPT_RUN_AGAIN_REFLECTOR="Reflector has already been run. Do you want to run it again? (y/N) "
  MSG_PROMPT_RUN_AGAIN_INSTALL="Base installation is already done. Do you want to run it again? (y/N) "

  # B-reflector.sh
  MSG_ALMOST_FORGOT="Oh, I almost forgot to run reflector, hold on, it will be quick"
  MSG_TYPING_SOUNDS="[typing sounds]"
  MSG_INSTALLING="Oh no... reflector is not installed, let me install it real quick"
  MSG_COMMAND_IS="Damn, that's a long command... here it is:"
  FINALIZESC="Fuck yeah, thats finally done"

  # C-instalacao.sh
  MSG_CONTINUE="Alright, mirrors updated. Let's continue..."
  MSG_SHOW_PKGS="Now I'll show you the essential packages..."
  MSG_WANT_MORE="Do you want to add more packages? (Y/n) "
  MSG_PKG_NAME="Enter the package name: "
  MSG_NOT_FOUND="Package not found."
  MSG_ADDING="Adding"
  MSG_ALREADY_SELECTED="Package already selected or already in the file."
  MSG_ANY_MORE="Any more? (Y/n) "
  MSG_WHICH_REPO="Which repository do you want to use? (extra, multilib, cachy) "
  MSG_TRY_AGAIN="Try again: "

  # D-regiao.sh
  MSG_START="Alright, let's configure your system's region and language."
  MSG_TIMEZONE_INFO="First, the timezone. You can see a list with 'timedatectl list-timezones'."
  MSG_TIMEZONE_PROMPT="Enter your timezone (e.g., America/New_York): "
  DEFAULT_REGION="America/New_York"
  MSG_INVALID_REGION="Invalid timezone! The file for that region does not exist in /usr/share/zoneinfo/. Please try again."
  MSG_LOCALE_INFO="Now, let's set up the locale and keyboard layout (keymap)."
  MSG_LOCALE_PROMPT="Enter your main locale (e.g., en_US): "
  DEFAULT_LOCALE="en_US"
  MSG_ADD_ANOTHER_LOCALE="Do you want to add another locale to be generated by the system? (Y/n) "
  MSG_NEXT_LOCALE_PROMPT="Enter the next locale (e.g., en_US): "
  MSG_KEYMAP_PROMPT="Enter your keyboard layout (e.g., us): "
  DEFAULT_KEYMAP="us"
  MSG_CONFIG_SAVED="Region settings saved to your plugin."

  # E-personalizacao.sh
  MSG_HOSTNAME_PROMPT="Alright, give your PC a name... and please, make it a nice one... "
  MSG_INVALID_HOSTNAME="Invalid name. Only letters, numbers, dot or hyphen. Try again: "
  MSG_RUNNING_MKINITCPIO="Running mkinitcpio -P..."
  MSG_MKINITCPIO_DONE="ALRIGHT DAMMIT, it's done. Now let's set your root password (no 1234, you fool)."
  MSG_SET_USER="Now tell me your username, let's create it and add it to the sudoers."
  MSG_USERNAME_PROMPT="Your username: "
  MSG_INVALID_USERNAME="Invalid username. Must start with a lowercase letter and contain only lowercase letters, numbers, _ or -. Try again: "
  MSG_WANT_DOTS="Do you have any dotfiles or nah? (Y/n)"

  # F-bootloader.sh
  MSG_START_BOOTLOADER="Alright, now for the final part, are you ready?"
  MSG_CONFIGURING="Configuring the bootloader via Ansible..."
  MSG_ENABLE_NETWORK="Enabling NetworkManager to start on boot..."
  MSG_GOODBYE_1="Alright, my job here is done, now it's up to you. In theory, you just need to reboot."
  MSG_GOODBYE_2="If something goes wrong, it's not my fault! Just kidding, I tried to make the script solid."
  MSG_GOODBYE_3="If you find a bug, open an issue on GitHub. Thanks for using Ch-aronte!"

  # G-dotfiles.sh
  MSG_LOADING_DOTS="Ight, loading ya dots."
  ;;
*)
  echo "Language not recognized. Please set LANGC to either 'Portugues' or 'English'"
  exit 1
  ;;
esac

# ==============================================================================
# FUNÇÕES DE UI
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

prompt_for_bootloader() {
  local bootloader_var
  while true; do
    read -p "$MSG_BOOTLOADER_PROMPT" -r bootloader_var
    bootloader_var=$(echo "$bootloader_var" | tr '[:upper:]' '[:lower:]')
    if [[ "$bootloader_var" == "grub" ]]; then
      break
    elif [[ "$bootloader_var" == "refind" && "$firmware" == "UEFI" ]]; then
      break
    elif [[ "$bootloader_var" == "refind" && "$firmware" == "BIOS" ]]; then
      echo "$MSG_INVALID_BOOTLOADER_BIOS"
    else
      echo "$MSG_INVALID_BOOTLOADER"
    fi
  done
  echo "$bootloader_var"
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
