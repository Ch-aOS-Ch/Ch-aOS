#!/bin/bash
set -e
set -a
source respostas.env
set +a
source scripts/resources.sh

# ==============================================================================
# SETUP DE IDIOMA E VARIÁVEIS
# ==============================================================================
case "$LANGC" in
"Portugues")
  MSG_HOSTNAME_PROMPT="ok, me dá um nome pro seu pc aí... e pelo amor de deus, me dá um nome bonito... "
  MSG_INVALID_HOSTNAME="Nome inválido. Só letras, números, ponto ou hífen. Tenta de novo aí oh jegue: "
  MSG_RUNNING_MKINITCPIO="rodando mkinitcpio -P..."
  MSG_MKINITCPIO_DONE="aí sim porra, rodou. Agora vamo settar tua senha de root (sem 1234 seu jegue)"
  MSG_SET_USER="agora me fala teu user, vamo criar e tacar ele lá no sudoers"
  MSG_USERNAME_PROMPT="Nome do teu usuário: "
  MSG_INVALID_USERNAME="Nome de usuário inválido. Deve começar com letra minúscula e conter apenas letras minúsculas, números, _ ou -. Mals aí "
  MSG_WANT_DOTS="Você tem alguma dotfile ou nem? (S/n)"
  ;;
"English")
  MSG_HOSTNAME_PROMPT="Alright, give your PC a name... and please, make it a nice one... "
  MSG_INVALID_HOSTNAME="Invalid name. Only letters, numbers, dot or hyphen. Try again: "
  MSG_RUNNING_MKINITCPIO="Running mkinitcpio -P..."
  MSG_MKINITCPIO_DONE="ALRIGHT DAMMIT, it's done. Now let's set your root password (no 1234, you fool)."
  MSG_SET_USER="Now tell me your username, let's create it and add it to the sudoers."
  MSG_USERNAME_PROMPT="Your username: "
  MSG_INVALID_USERNAME="Invalid username. Must start with a lowercase letter and contain only lowercase letters, numbers, _ or -. Try again: "
  MSG_WANT_DOTS="Do you have any dotfiles or nah? (Y/n)"
  ;;
*)
  echo "Language not recognized. Exiting."
  exit 1
  ;;
esac

SECRETS_FILE="plugins/secrets_""$PLUGIN"

# ==============================================================================
# FLUXO PRINCIPAL DO SCRIPT
# ==============================================================================

read -p "$MSG_HOSTNAME_PROMPT" -r hostname
while [[ -z "$hostname" || "$hostname" =~ [^a-zA-Z0-9.-] ]]; do
  read -p "$MSG_INVALID_HOSTNAME" -r hostname
done
yq -iy ".hostname = \"$hostname\"" "plugins/$PLUGIN"

sleep 1

echo "$MSG_RUNNING_MKINITCPIO"
arch-chroot /mnt mkinitcpio -P
echo ""
sleep 1
echo "$MSG_MKINITCPIO_DONE"

sleep 1

echo "$MSG_SET_USER"
read -p "$MSG_USERNAME_PROMPT" -r username

# A VALIDAÇÃO ADICIONADA ESTÁ AQUI
while [[ -z "$username" || ! "$username" =~ ^[a-z_][a-z0-9_-]*$ ]]; do
  read -p "$MSG_INVALID_USERNAME" -r username
done

# Adiciona a lista de usuários com yq de forma estruturada
yq -iy '.users = [
  {
    "name": "'$username'",
    "shell": "/bin/bash",
    "groups": ["wheel", "'$username'"],
  },
  {
    "name": "root",
    "shell": "/bin/bash",
    "groups": ["root"],
  }
]' "plugins/$plugin"

echo "$SECRETS_FILE" >>.gitignore && touch $SECRETS_FILE
echo "{}" >"$SECRETS_FILE"
yq -iy ".secrets = \"$SECRETS_FILE\"" "plugins/$PLUGIN"

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
  user_hash=$(printf '%s' "$user_pass" | python -c "import crypt, sys; print(crypt.crypt(sys.stdin.read(), crypt.METHOD_SHA512))")
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
yq -iy '.wheel_access = true' "plugins/$PLUGIN"

read -rp "$MSG_WANT_DOTS" dot_accept
if [[ $dot_accept != "N" && $dot_accept != "n" ]]; then
  chmod +x scripts/G-dotfiles.sh
  bash scripts/G-dotfiles.sh
fi

set -a
source respostas.env
set +a

rm -rf ./.git
rm -rf /mnt/root/Ch-aronte/
cp -r ../Ch-aronte /mnt/root/Ch-aronte
arch-chroot /mnt ansible-playbook -vvv /root/Ch-aronte/main.yaml --tags config -e @plugins/"$PLUGIN"

# --- Encadeia o próximo script ---
echo "Configuração finalizada. Passando para a instalação do bootloader..."
chmod +x scripts/F-bootloader.sh
bash scripts/F-bootloader.sh
