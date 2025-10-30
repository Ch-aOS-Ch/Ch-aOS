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
echo '{"user_secrets": {}}' >"$SECRETS_FILE"
plugin_set_value "secrets.sec_file" "$SECRETS_FILE"
plugin_set_value "secrets.sec_mode" "charonte"

clear
echo "Senha para o usuário: ${username}"
echo "Como deseja configurar a senha?"
echo "1" "Digitar agora e salvar em COFRE (SOPS com texto hasheado, nix like)"
echo "2" "Digitar agora e salvar como HASH plain text"
echo "3" "Digitar agora e não salvar em cofre (Plain Text, Extremamente inseguro, mas fácil de ler)"
echo "4" "Não definir senha agora (configuração manual pós-reboot)"
read -r choice

plugin_set_value "secrets.sec_mode" "charonte"

case $choice in
"2")
	read -srp "Digite a senha para '${username}': " user_pass
	echo ""
	user_hash=$(printf '%s' "$user_pass" | openssl passwd -6 -stdin)
	yq -iy ".user_secrets.${username}.password = \"$user_hash\"" "$SECRETS_FILE"
	yq -iy ".user_secrets.root.password = \"$user_hash\"" "$SECRETS_FILE"
	;;
"1")
	read -srp "Digite a senha para '${username}': " user_pass
	echo ""
	user_hash=$(printf '%s' "$user_pass" | openssl passwd -6 -stdin)
	yq -iy ".user_secrets.${username}.password = \"$user_hash\"" "$SECRETS_FILE"
	yq -iy ".user_secrets.root.password = \"$user_hash\"" "$SECRETS_FILE"
	USE_SOPS=true
	plugin_set_value "secrets.sec_mode" "sops"
	;;
"3")
	read -srp "Digite a senha para '${username}': " user_pass
	echo ""
	yq -iy ".user_secrets.${username}.password = \"$user_pass\"" "$SECRETS_FILE"
	yq -iy ".user_secrets.root.password = \"$user_pass\"" "$SECRETS_FILE"

	;;
"4")
	yq -iy ".user_secrets.${username} = {}" "$SECRETS_FILE"
	yq -iy ".user_secrets.root = {}" "$SECRETS_FILE"
	echo "Lembre-se de definir a senha para '${username}' manualmente após o reboot." >&2
	;;
esac

if [ "$USE_SOPS" = true ]; then
	echo "Configurando SOPS. Primeiro, vamos gerar uma chave PGP para você." >&2

	read -rp "Digite seu nome completo (para a chave PGP): " pgp_name
	read -rp "Digite seu email (para a chave PGP): " pgp_email
	while [[ -z "$pgp_name" || -z "$pgp_email" ]]; do
		echo "Nome e email não podem ser vazios." >&2
		read -rp "Digite seu nome completo: " pgp_name
		read -rp "Digite seu email: " pgp_email
	done

	echo "Gerando uma chave PGP de 4096 bits para '${pgp_name} <${pgp_email}>'..." >&2
	echo "Você será solicitado a criar uma SENHA para esta chave. Guarde-a bem." >&2

	# Batch file for GPG
	gpg_batch_input=$(
		cat <<EOF
Key-Type: RSA
Key-Length: 4096
Subkey-Type: RSA
Subkey-Length: 4096
Name-Real: ${pgp_name}
Name-Email: ${pgp_email}
Expire-Date: 0
%commit
EOF
	)

	# Generate key - this will prompt for a passphrase
	echo "$gpg_batch_input" | gpg --batch --generate-key

	# Get fingerprint
	fingerprint=$(gpg --list-secret-keys --with-colons "${pgp_email}" | grep '^fpr' | cut -d: -f10)

	if [ -z "$fingerprint" ]; then
		echo "ERRO: Não foi possível obter o fingerprint da chave PGP gerada. Abortando." >&2
		exit 1
	fi

	echo "Chave PGP gerada com sucesso. Fingerprint: ${fingerprint}" >&2

	# Create sops-config.yml
	SOPS_CONFIG_FILE="Ch-obolos/sops-config.yml"
	cat <<EOF >"$SOPS_CONFIG_FILE"
creation_rules:
- path_regex: (.*)?/secrets_.*\\.yml$
    pgp: '${fingerprint}'
EOF
	echo "Arquivo de configuração SOPS criado em '$SOPS_CONFIG_FILE'." >&2

	# Encrypt the secrets file
	echo "Criptografando o arquivo de segredos '$SECRETS_FILE' com SOPS..." >&2
	echo "Você precisará digitar a senha da sua chave PGP agora." >&2
	sops --config "$SOPS_CONFIG_FILE" --encrypt --in-place "$SECRETS_FILE"
	echo "Arquivo '$SECRETS_FILE' criptografado com sucesso." >&2

	echo "Copiando seu keyring para seu novo sistema" >&2
	mkdir -p /mnt/root/.gnupg/
	cp -a /root/.gnupg/* /mnt/root/.gnupg/
	echo "Cópia concluida" >&2
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

echo "Configuração finalizada. Passando para a instalação do bootloader..."
