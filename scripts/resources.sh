set_env_var() {
  local var="$1"
  local val="$2"
  if grep -q "^${var}=" "$envfile"; then
    sed -i "s|^${var}=.*|${var}=${val}|" "$envfile"
  else
    echo "${var}=${val}" >> "$envfile"
  fi
}
