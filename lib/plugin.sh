#!/bin/bash

PLUGIN_DIR="./Ch-obolos/"
touch respostas.env

set_env_var() {
  local envvar="$1"
  local value="$2"
  echo "$envvar=$value" >>respostas.env
}

# Função para definir um valor em um arquivo de plugin usando yq
# Uso: plugin_set_value "caminho.para.chave" "valor"
plugin_set_value() {
  local key_path="$1"
  local value="$2"
  yq -iy ".${key_path} = \"${value}\"" "${PLUGIN_DIR}${PLUGIN}"
}

# Adiciona um item a uma lista, garantindo que a lista seja única
# Uso: plugin_add_to_list_unique "caminho.para.lista" "valor"
plugin_add_to_list_unique() {
  local key_path="$1"
  local value="$2"
  yq -iy ".${key_path} += [\"${value}\"] | .${key_path} |= unique" "${PLUGIN_DIR}${PLUGIN}"
}

# Adiciona um item a uma lista
# Uso: plugin_add_to_list "caminho.para.lista" "valor"
plugin_add_to_list() {
  local key_path="$1"
  local value="$2"
  yq -iy ".${key_path} += [\"${value}\"]" "${PLUGIN_DIR}${PLUGIN}"
}

# Função para selecionar um plugin existente ou criar um novo
select_or_create_plugin_file() {
  shopt -s nullglob
  mkdir -p "$PLUGIN_DIR"
  local existing_plugins=("${PLUGIN_DIR}"custom*.yml)
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
    while [[ -z "$arquivo" || ! -f "$PLUGIN_DIR$arquivo" ]]; do
      echo "$MSG_INVALID_FILE" >&2
      for file in "${existing_plugins[@]}"; do basename "$file"; done >&2
      read -rp "$MSG_PROMPT_WHICH_PLUGIN" arquivo
    done
    echo "$MSG_USING_EXISTING $arquivo" >&2
    set_env_var "PLUGIN" "$arquivo"
  else
    local qtd
    qtd=$(find "$PLUGIN_DIR" -maxdepth 1 -type f -name 'custom*.yml' | wc -l)
    arquivo="custom$((qtd + 1)).yml"
    echo "{}" >"$PLUGIN_DIR$arquivo"
    echo "$MSG_CREATING_NEW $arquivo" >&2
    set_env_var "PLUGIN_PATH" "$HOME/Ch-aronte/$PLUGIN_DIR$arquivo"
    set_env_var "CHOICE" "$choice"
  fi
  echo "$arquivo"
}

# função para atualizar repositórios extras
repos_update() {
  local want_repo
  read -p "Deseja configurar repositórios extras (multilib, cachy, etc)? (Y/n) " -r want_repo
  if [[ "$want_repo" == "n" || "$want_repo" == "N" ]]; then
    return
  fi

  # Inicializa a estrutura no YAML para evitar erros
  yq -iy '.repos.managed.extras |= (select(.) // false)' "Ch-obolos/$PLUGIN"
  yq -iy '.repos.third_party |= (select(.) // [])' "Ch-obolos/$PLUGIN"

  want_repo="y"
  while [[ "$want_repo" =~ ^[Yy]?$ ]]; do
    read -p "$MSG_WHICH_REPO" -r repo
    local repo_name
    repo_name=$(echo "$repo" | tr '[:upper:]' '[:lower:]')

    case $repo_name in
    "multilib" | "extra")
      echo "$MSG_ADDING $repo_name..."
      plugin_set_value "repos.managed.extras" "true"
      ;;
    "cachyos" | "cachy")
      if yq -e '.repos.third_party[] | select(.name == "cachyos")' "Ch-obolos/$PLUGIN" >/dev/null; then
        echo "$MSG_ALREADY_SELECTED"
      else
        echo "Iniciando bootstrap dos repositórios CachyOS no sistema de destino..."

        local tmp_dir
        tmp_dir=$(mktemp -d)

        echo "Baixando o script de instalação..."
        curl -L https://mirror.cachyos.org/cachyos-repo.tar.xz -o "$tmp_dir/cachyos-repo.tar.xz"
        tar xvf "$tmp_dir/cachyos-repo.tar.xz" -C "$tmp_dir"

        echo "Copiando script para o chroot e executando..."
        arch-chroot /mnt mkdir -p /tmp
        cp -r "$tmp_dir/cachyos-repo" "/mnt/tmp/"
        arch-chroot /mnt /tmp/cachyos-repo/cachyos-repo.sh

        echo "Limpando arquivos temporários..."
        rm -rf "$tmp_dir"
        arch-chroot /mnt rm -rf /tmp/cachyos-repo

        echo "Bootstrap do CachyOS concluído. Sincronizando pacman dentro do chroot..."
        arch-chroot /mnt pacman -Sy

        echo "Adicionando configuração declarativa do CachyOS ao plugin..."
        plugin_add_to_list_unique "pacotes" "cachyos-keyring"
        plugin_add_to_list_unique "pacotes" "cachyos-mirrorlist"
        plugin_add_to_list_unique "pacotes" "cachyos-v3-mirrorlist"
        yq -iy '.repos.third_party += [{"name": "cachyos", "include": "/etc/pacman.d/cachyos-mirrorlist"}]' "Ch-obolos/$PLUGIN"
        yq -iy '.repos.third_party += [{"name": "cachyos-v3", "include": "/etc/pacman.d/cachyos-v3-mirrorlist"}]' "Ch-obolos/$PLUGIN"
        yq -iy '.repos.third_party += [{"name": "cachyos-core-v3", "include": "/etc/pacman.d/cachyos-v3-mirrorlist"}]' "Ch-obolos/$PLUGIN"
        yq -iy '.repos.third_party += [{"name": "cachyos-extra-v3", "include": "/etc/pacman.d/cachyos-v3-mirrorlist"}]' "Ch-obolos/$PLUGIN"
      fi
      ;;
    *)
      echo "Repositório inválido. Tente novamente."
      ;;
    esac
    read -p "$MSG_ANY_MORE" -r want_repo
  done
}
