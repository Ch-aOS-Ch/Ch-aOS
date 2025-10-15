#!/bin/bash
envfile="respostas.env"
set_env_var() {
  local var="$1"
  local val="$2"

  # Escapa os caracteres especiais para o `sed`
  local escaped_val
  escaped_val=$(printf '%s\n' "$val" | sed -e 's/[&\\|]/\\&/g')

  if grep -q "^${var}=" "$envfile"; then
    sed -i "s|^${var}=.*|${var}=${escaped_val}|" "$envfile"
  else
    echo "${var}=${val}" >>"$envfile"
  fi
}
set_yml_var() {
  local config_file="$1"
  local key="$2"
  local value="$3"

  mkdir -p "$(dirname "$config_file")"

  touch "$config_file"

  local escaped_value
  escaped_value=$(printf '%s\n' "$value" | sed -e 's/[&\\|]/\\&/g')

  if grep -q "^${key}:" "$config_file"; then
    sed -i "s|^${key}:.*|${key}: '${escaped_value}'|" "$config_file"
  else
    echo "${key}: '${value}'" >>"$config_file"
  fi
}
