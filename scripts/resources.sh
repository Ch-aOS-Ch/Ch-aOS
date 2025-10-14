#!/bin/bash
envfile="respostas.env"
set_env_var() {
  local var="$1"
  local val="$2"
  if grep -q "^${var}=" "$envfile"; then
    sed -i "s|^${var}=.*|${var}=${val}|" "$envfile"
  else
    echo "${var}=${val}" >>"$envfile"
  fi
}
set_yml_var() {
  local config_file="$1"
  local key="$2"
  local value="$3"

  # Garante que o diretório de configuração exista
  mkdir -p "$(dirname "$config_file")"

  # Garante que o arquivo de configuração exista
  touch "$config_file"

  if grep -q "^${key}:" "$config_file"; then
    sed -i "s|^${key}:.*|${key}: '${value}'|" "$config_file"
  else
    echo "${key}: '${value}'" >>"$config_file"
  fi
}
