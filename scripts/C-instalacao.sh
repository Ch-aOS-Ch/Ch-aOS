#!/bin/bash
set -a
source respostas.env
set +a
pacotes=()
source ./scripts/resources.sh

# --- SEÇÃO DE CONFIGURAÇÃO DE IDIOMA ---
case "$LANGC" in
"Portugues")
  MSG_CONTINUE="Beleza, mirrors atualizados. Bora continuar..."
  MSG_SHOW_PKGS="Ok, agora vou te mostrar os pacotes essenciais..."
  MSG_WANT_MORE="quer mais algum pacote? (Y/n) "
  MSG_LETS_ADD="Ok, vamos adicionar mais pacotes!"
  MSG_CONTINUE_WITHOUT="Ok, vamos continuar sem mais pacotes adicionais."
  MSG_PKG_NAME="Digite o nome do pacote: "
  MSG_PKG_NOT_FOUND="Pacote não encontrado."
  MSG_TRY_AGAIN="Digite novamente:"
  MSG_ADDING="Adicionando"
  MSG_ALREADY_SELECTED="pacote já selecionado"
  MSG_ANY_MORE="mais algum? (Y/n) "
  MSG_CHOSEN_LIST="Lista dos pacotes que você escolheu:"
  ;;
"English")
  MSG_CONTINUE="Alright, mirrors updated. Let's continue..."
  MSG_SHOW_PKGS="Now I'll show you the essential packages..."
  MSG_WANT_MORE="Do you want to add more packages? (Y/n) "
  MSG_LETS_ADD="Okay, let's add more packages!"
  MSG_CONTINUE_WITHOUT="Okay, let's continue without additional packages."
  MSG_PKG_NAME="Enter the package name: "
  MSG_PKG_NOT_FOUND="Package not found."
  MSG_TRY_AGAIN="Please enter again:"
  MSG_ADDING="Adding"
  MSG_ALREADY_SELECTED="Package already selected."
  MSG_ANY_MORE="Any more? (Y/n) "
  MSG_CHOSEN_LIST="List of packages you chose:"
  ;;
*)
  echo "Unsupported language setting."
  bash scripts/C-instalacao.sh
  exit 1
  ;;
esac

# --- FLUXO PRINCIPAL DO SCRIPT ---
echo "$MSG_CONTINUE"
echo ""
echo "$MSG_SHOW_PKGS"
sleep 1
echo "---------------------------------------------------"
echo "Pacotes necessários / Required packages:"
echo "  - base, base-devel, linux, linux-firmware, linux-headers"
echo "  - reflector, refind, nano, networkmanager, openssh"
echo "---------------------------------------------------"
sleep 1

read -p "$MSG_WANT_MORE" -r ok
set_env_var "PLUGIN_ACCEPT" "$ok"

if [[ "$ok" == "Y" || "$ok" == "y" || "$ok" == "" ]]; then
  echo "$MSG_LETS_ADD"

  plugin_dir="./roles/sistema/vars/"
  mkdir -p "$plugin_dir"
  qtd=$(find "$plugin_dir" -maxdepth 1 -type f -name 'custom*.yml' | wc -l)
  arquivo="custom$((qtd + 1)).yml"

  set_env_var "PLUGIN" "$HOME/Ch-aronte/$plugin_dir$arquivo"
  echo "pacotes:" >"$plugin_dir$arquivo"

  while [[ "$ok" == "Y" || "$ok" == "y" || "$ok" == "" ]]; do
    read -p "$MSG_PKG_NAME" -r pacote
    while ! pacman -Ss "$pacote" >/dev/null 2>&1; do
      echo "$MSG_PKG_NOT_FOUND"
      echo "$MSG_TRY_AGAIN"
      read -p "$MSG_PKG_NAME" -r pacote
    done

    if [[ ! " ${pacotes[*]} " =~ " $pacote " ]]; then # Espaços evitam matches parciais
      echo "$MSG_ADDING $pacote..."
      pacotes+=("$pacote")
      echo "  - $pacote" >>"$plugin_dir$arquivo"
    else
      echo "$MSG_ALREADY_SELECTED"
    fi
    read -p "$MSG_ANY_MORE" -r ok
  done

  echo ""
  echo "$MSG_CHOSEN_LIST"
  printf '%s\n' "${pacotes[@]}"
else
  echo "$MSG_CONTINUE_WITHOUT"
fi

echo ""
echo "Starting Ansible playbook..."
set -a
source respostas.env
set +a
ansible-playbook -vvv ./main.yaml --tags instalacao
genfstab -U /mnt >>/mnt/etc/fstab
