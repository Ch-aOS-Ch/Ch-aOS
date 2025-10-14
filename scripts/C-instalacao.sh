#!/bin/bash
set -e
set -a
source respostas.env
set +a
source scripts/resources.sh

# Variáveis globais
pacotes=()
plugin_dir="./plugins/"

# --- SEÇÃO DE CONFIGURAÇÃO DE IDIOMA ---
case "$LANGC" in
"Portugues")
  MSG_CONTINUE="Beleza, mirrors atualizados. Bora continuar..."
  MSG_SHOW_PKGS="Ok, agora vou te mostrar os pacotes essenciais..."
  MSG_WANT_MORE="Quer mais algum pacote? (Y/n) "
  MSG_LETS_ADD="Ok, vamos adicionar mais pacotes!"
  MSG_PKG_NAME="Digite o nome do pacote: "
  MSG_PKG_NOT_FOUND="Pacote não encontrado."
  MSG_TRY_AGAIN="Digite novamente:"
  MSG_ADDING="Adicionando"
  MSG_ALREADY_SELECTED="Pacote já selecionado ou já presente no arquivo."
  MSG_ANY_MORE="Mais algum? (Y/n) "

  ;;
"English")
  MSG_CONTINUE="Alright, mirrors updated. Let's continue..."
  MSG_SHOW_PKGS="Now I'll show you the essential packages..."
  MSG_WANT_MORE="Do you want to add more packages? (Y/n) "
  MSG_LETS_ADD="Okay, let's add more packages!"
  MSG_PKG_NAME="Enter the package name: "
  MSG_PKG_NOT_FOUND="Package not found."
  MSG_TRY_AGAIN="Please enter again:"
  MSG_ADDING="Adding"
  MSG_ALREADY_SELECTED="Package already selected or already in the file."
  MSG_ANY_MORE="Any more? (Y/n) "

  ;;
*)
  echo "Unsupported language setting."
  exit 1
  ;;
esac

# --- FUNÇÕES ---

# Função para escolher ou criar plugin

add_packages_to_file() {
  local target_file="$1"
  local ok="y"
  local pacote
  echo "pacotes:" >>plugins/"$PLUGIN"

  while [[ "$ok" == "Y" || "$ok" == "y" || "$ok" == "" ]]; do
    read -p "$MSG_PKG_NAME" -r pacote
    while ! pacman -Ss "$pacote" >/dev/null 2>&1; do
      echo "$MSG_PKG_NOT_FOUND"
      read -p "$MSG_TRY_AGAIN" -r pacote
    done

    if ! grep -q -- "- $pacote" "$plugin_dir$target_file" && [[ ! " ${pacotes[*]} " =~ " $pacote " ]]; then
      echo "$MSG_ADDING $pacote..."
      pacotes+=("$pacote")
      echo "  - $pacote" >>"$plugin_dir$target_file"
    else
      echo "$MSG_ALREADY_SELECTED"
    fi
    read -p "$MSG_ANY_MORE" -r ok
  done
}

# --- FLUXO PRINCIPAL DO SCRIPT ---
echo "$MSG_CONTINUE"
echo "$MSG_SHOW_PKGS"
sleep 1
echo "---------------------------------------------------"
echo "Pacotes necessários / Required packages:"
echo "  - base, base-devel, linux, linux-firmware, linux-headers"
echo "  - reflector, bootloader(grub ou refind), nano, networkmanager, openssh"
echo "---------------------------------------------------"
sleep 1

add_packages_to_file "plugins/$PLUGIN"

echo ""
echo "Starting Ansible playbook..."
set -a
source respostas.env
set +a
ansible-playbook -vvv ./main.yaml --tags instalacao -e @plugins/"$PLUGIN"
genfstab -U /mnt >/mnt/etc/fstab
