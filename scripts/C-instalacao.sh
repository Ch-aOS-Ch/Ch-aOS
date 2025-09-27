#!/bin/bash
set -a
source respostas.env
set +a
source scripts/resources.sh

# Variáveis globais
pacotes=()
plugin_dir="./roles/sistema/vars/"

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

  # Mensagens específicas da lógica de plugin
  MSG_EXISTING_PLUGINS_FOUND="Plugins existentes foram encontrados:"
  MSG_CHOICE_PROMPT="Deseja criar um NOVO plugin ou usar um EXISTENTE? (novo/usar): "
  MSG_PROMPT_WHICH_PLUGIN="Digite o nome do plugin que você quer usar (ex: custom1.yml): "
  MSG_INVALID_FILE="Arquivo inválido ou não encontrado. Por favor, escolha um da lista."
  MSG_USING_EXISTING="Usando o plugin existente:"
  MSG_CREATING_NEW="Criando novo plugin:"
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

  # Plugin-specific logic messages
  MSG_EXISTING_PLUGINS_FOUND="Existing plugins were found:"
  MSG_CHOICE_PROMPT="Do you want to create a NEW plugin or USE an existing one? (new/use): "
  MSG_PROMPT_WHICH_PLUGIN="Enter the name of the plugin you want to use (e.g., custom1.yml): "
  MSG_INVALID_FILE="Invalid file or not found. Please choose one from the list."
  MSG_USING_EXISTING="Using existing plugin:"
  MSG_CREATING_NEW="Creating new plugin:"
  ;;
*)
  echo "Unsupported language setting."
  exit 1
  ;;
esac

# --- FUNÇÕES ---

# Função para escolher ou criar plugin

select_or_create_plugin_file() {
  shopt -s nullglob
  mkdir -p "$plugin_dir"

  local existing_plugins=("$plugin_dir"custom*.yml)
  local choice arquivo

  if [ ${#existing_plugins[@]} -gt 0 ]; then
    # Imprime na saída de erro (stderr) para aparecer na tela
    echo "$MSG_EXISTING_PLUGINS_FOUND" >&2
    for file in "${existing_plugins[@]}"; do
      basename "$file"
    done >&2 # Redireciona a saída do loop inteiro

    echo "" >&2 # Linha em branco também para stderr
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
      for file in "${existing_plugins[@]}"; do
        basename "$file"
      done >&2
      read -rp "$MSG_PROMPT_WHICH_PLUGIN" arquivo
    done
    echo "$MSG_USING_EXISTING $arquivo" >&2
    set_env_var "PLUGIN" "$plugin_dir$arquivo"
  else
    local qtd
    qtd=$(find "$plugin_dir" -maxdepth 1 -type f -name 'custom*.yml' | wc -l)
    arquivo="custom$((qtd + 1)).yml"

    echo "$MSG_CREATING_NEW $arquivo" >&2
    set_env_var "PLUGIN" "$HOME/Ch-aronte/$plugin_dir$arquivo"
    echo "pacotes:" >"$plugin_dir$arquivo"
  fi

  # Este é o único echo que vai para a saída padrão (stdout).
  # Ele será o valor retornado para a variável 'arquivo_plugin'.
  echo "$arquivo"
}

add_packages_to_file() {
  local target_file="$1"
  local ok="y"
  local pacote

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

read -p "$MSG_WANT_MORE" -r ok_plugin
set_env_var "PLUGIN_ACCEPT" "$ok_plugin"

if [[ "$ok_plugin" == "Y" || "$ok_plugin" == "y" || "$ok_plugin" == "" ]]; then
  arquivo_plugin=$(select_or_create_plugin_file)
  add_packages_to_file "$arquivo_plugin"
fi

echo ""
echo "Starting Ansible playbook..."
set -a
source respostas.env
set +a
ansible-playbook -vvv ./main.yaml --tags instalacao
genfstab -U /mnt >>/mnt/etc/fstab
