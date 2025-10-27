#!/bin/bash
set -e

source ./lib/ui.sh
source ./lib/plugin.sh
source ./scripts/resources.sh
set -a
source ./respostas.env
set +a

SECRETS_FILE="Ch-obolos/secrets_""$PLUGIN"

# ==============================================================================
# FLUXO PRINCIPAL DO SCRIPT
# ==============================================================================

read -p "$MSG_HOSTNAME_PROMPT" -r hostname
while [[ -z "$hostname" || "$hostname" =~ [^a-zA-Z0-9.-] ]]; do
  read -p "$MSG_INVALID_HOSTNAME" -r hostname
done
plugin_set_value "hostname" "$hostname"

sleep 1

sleep 1

echo "$MSG_SET_USER"
read -p "$MSG_USERNAME_PROMPT" -r username

# A VALIDAÇÃO ADICIONADA ESTÁ AQUI
while [[ -z "$username" || ! "$username" =~ ^[a-z_][a-z0-9_-]*$ ]]; do
  read -p "$MSG_INVALID_USERNAME" -r username
done

# Adiciona a lista de usuários com yq de forma estruturada
# Nota: Esta estrutura complexa é mantida aqui por clareza, em vez de uma função de helper genérica.
yq -iy '.users = [
  {
    "name": "'$username'",
    "shell": "bash",
    "groups": ["wheel"],
  },
  {
    "name": "root",
    "shell": "bash",
    "groups": ["root"],
  }
]' "Ch-obolos/$PLUGIN"

echo "$SECRETS_FILE" >>.gitignore && touch "$SECRETS_FILE"
echo "{}" >"$SECRETS_FILE"
plugin_set_value "secrets.sec_file" "$SECRETS_FILE"
plugin_set_value "secrets.sec_mode" "charonte"

clear
echo "Senha para o usuário: ${username}"
echo "Como deseja configurar a senha?"
echo "1" "Digitar agora e salvar como HASH (Recomendado, Nix-like)"
echo "2" "Digitar agora e salvar em COFRE (Vault com texto puro)"
echo "3" "Digitar agora e não salvar em cofre (Plain Text, Extremamente inseguro, mas fácil de ler)"
echo "4" "Não definir senha agora (configuração manual pós-reboot)"
read -r choice

case $choice in
"1")
  read -srp "Digite a senha para '${username}': " user_pass
  echo ""
  user_hash=$(printf '%s' "$user_pass" | openssl passwd -6 -stdin)
  yq -iy ".${username}.password = \"$user_hash\"" "$SECRETS_FILE"
  yq -iy ".root.password = \"$user_hash\"" "$SECRETS_FILE"
  ;;
"2")
  read -srp "Digite a senha para '${username}': " user_pass
  echo ""
  yq -iy ".${username}.password = \"$user_pass\"" "$SECRETS_FILE"
  yq -iy ".root.password = \"$user_pass\"" "$SECRETS_FILE"
  USE_VAULT=true
  ;;
"3")
  read -srp "Digite a senha para '${username}': " user_pass
  echo ""
  yq -iy ".${username}.password = \"$user_pass\"" "$SECRETS_FILE"
  yq -iy ".root.password = \"$user_pass\"" "$SECRETS_FILE"

  ;;
"4")
  yq -iy ".${username} = {}" "$SECRETS_FILE"
  yq -iy ".root = {}" "$SECRETS_FILE"
  echo "Lembre-se de definir a senha para '${username}' manualmente após o reboot." >&2
  ;;
esac

if [ "$USE_VAULT" = true ]; then
  echo "Uma ou mais senhas foram salvas em texto puro." >&2
  echo "Vamos criptografar o arquivo 'segredos.yml' com o Ansible Vault." >&2
  echo "Por favor, crie uma senha para o seu cofre (vault)." >&2
  ansible-vault encrypt "$SECRETS_FILE"
  echo "Arquivo '$SECRETS_FILE' criptografado com sucesso." >&2
fi

echo "$SECRETS_FILE" >>./.gitignore
# ==============================================================================
# LÓGICA COMPARTILHADA FINAL
# ==============================================================================

# --- Habilita o Sudo para o grupo 'wheel' ---
echo "Habilitando privilégios de superusuário (sudo) para o novo usuário..."
plugin_set_value "wheel_access" "true"

if [[ $CHOICE = "usar" || $CHOICE = "use" ]]; then
  read -rp "$MSG_WANT_DOTS" dot_accept
  if [[ $dot_accept != "N" && $dot_accept != "n" ]]; then
    export DOTS_ACCEPT="yes"
  fi
fi

# --- Encadeia o próximo script ---
echo "Configuração finalizada. Passando para a instalação do bootloader..."
