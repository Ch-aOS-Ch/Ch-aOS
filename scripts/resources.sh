#!/bin/bash
envfile="respostas.env"
set_env_var() {
  local var="$1"
  local val="$2"
  if grep -q "^${var}=" "$envfile"; then
    sed -i "s|^${var}=.*|${var}=${val}\n|" "$envfile"
  else
    echo "${var}=${val}\n" >>"$envfile"
  fi
}
