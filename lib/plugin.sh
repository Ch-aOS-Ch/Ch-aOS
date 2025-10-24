#!/bin/bash

PLUGIN_DIR="./Ch-obolos/"

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
  local existing_plugins=(${PLUGIN_DIR}custom*.yml)
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
