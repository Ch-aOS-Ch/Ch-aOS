#!/bin/bash
set -e
set -a
source respostas.env
set +a
source scripts/resources.sh

# Variáveis globais
plugin_dir="./plugins/"

# --- SEÇÃO DE CONFIGURAÇÃO DE IDIOMA ---
case "$LANGC" in
"Portugues")
  MSG_CONTINUE="Beleza, mirrors atualizados. Bora continuar..."
  MSG_SHOW_PKGS="Ok, agora vou te mostrar os pacotes essenciais..."
  MSG_WANT_MORE="Quer mais algum pacote? (Y/n) "
  MSG_PKG_NAME="Digite o nome do pacote: "
  MSG_NOT_FOUND="Pacote não encontrado."
  MSG_ADDING="Adicionando"
  MSG_ALREADY_SELECTED="Pacote já selecionado ou já presente no arquivo."
  MSG_ANY_MORE="Mais algum? (Y/n) "
  MSG_WHICH_REPO="Qual repositório você quer usar? (extra, multilib, cachy) "
  MSG_TRY_AGAIN="Tente novamente: "
  ;;
"English")
  MSG_CONTINUE="Alright, mirrors updated. Let's continue..."
  MSG_SHOW_PKGS="Now I'll show you the essential packages..."
  MSG_WANT_MORE="Do you want to add more packages? (Y/n) "
  MSG_PKG_NAME="Enter the package name: "
  MSG_NOT_FOUND="Package not found."
  MSG_ADDING="Adding"
  MSG_ALREADY_SELECTED="Package already selected or already in the file."
  MSG_ANY_MORE="Any more? (Y/n) "
  MSG_WHICH_REPO="Which repository do you want to use? (extra, multilib, cachy) "
  MSG_TRY_AGAIN="Try again: "
  ;;
*)
  echo "Unsupported language setting."
  exit 1
  ;;
esac

# --- FUNÇÕES ---
repos_update() {
  local want_repo
  read -p "Deseja configurar repositórios extras (multilib, cachy, etc)? (Y/n) " -r want_repo
  if [[ "$want_repo" == "n" || "$want_repo" == "N" ]]; then
    return
  fi

  want_repo="y"
  while [[ "$want_repo" =~ ^[Yy]?$ ]]; do
    read -p "$MSG_WHICH_REPO" -r repo
    local repo_name
    repo_name=$(echo "$repo" | tr '[:upper:]' '[:lower:]')

    # Checa com yq se o repo já existe
    if yq -e ".repos[] | select(.name == \"$repo_name\")" "plugins/$PLUGIN" >/dev/null; then
      echo "$MSG_ALREADY_SELECTED"
      read -p "$MSG_ANY_MORE" -r want_repo
      continue
    fi

    case $repo_name in
    "multilib" | "extra")
      echo "$MSG_ADDING $repo_name..."
      yq -iy ".repos += [{\"name\": \"$repo_name\", \"state\": \"present\", \"method\": \"uncomment\"}]" "plugins/$PLUGIN"
      ;;
    "cachyos" | "cachy")
      echo "$MSG_ADDING cachyos..."
      local cachy_command="curl -L https://mirror.cachyos.org/cachyos-repo.tar.xz | tar xJ -C /tmp && /tmp/cachyos-repo/cachyos-repo.sh"
      yq -iy ".repos += [{\"name\": \"cachyos\", \"state\": \"present\", \"method\": \"script\", \"command\": \"$cachy_command\"}]" "plugins/$PLUGIN"
      ;;
    *)
      echo "Repositório inválido. Tente novamente."
      ;;
    esac
    read -p "$MSG_ANY_MORE" -r want_repo
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

# Garante que a chave 'pacotes' exista como uma lista no plugin
yq -iy '.pacotes |= (select(.) // [])' "plugins/$PLUGIN"

add_pkg="n"
read -p "$MSG_WANT_MORE" -r add_pkg
while [[ "$add_pkg" != "n" && "$add_pkg" != "N" ]]; do
  read -p "$MSG_PKG_NAME" -r pacote
  while ! pacman -Ss "$pacote" >/dev/null 2>&1; do
    echo "$MSG_NOT_FOUND"
    read -p "$MSG_TRY_AGAIN" -r pacote
  done

  # Adiciona o pacote à lista 'pacotes' de forma segura, sem duplicatas
  yq -iy ".pacotes += [\"$pacote\"] | .pacotes |= unique" "plugins/$PLUGIN"
  echo "$MSG_ADDING $pacote..."

  read -p "$MSG_ANY_MORE" -r add_pkg
done

# Garante que a chave 'repos' exista como uma lista e adiciona 'core'
yq -iy '.repos |= (select(.) // [])' "plugins/$PLUGIN"
yq -iy '.repos += [{"name": "core", "state": "present", "method": "uncomment"}] | .repos |= unique_by(.name)' "plugins/$PLUGIN"

repos_update

set -a
source respostas.env
set +a

# Copia o projeto para dentro do chroot para que o Ansible possa ser executado lá
cp -r ./ /mnt/root/Ch-aronte/

# Executa os playbooks em sequência, a maioria DENTRO do chroot
ansible-playbook -vvv ./main.yaml --tags instalacao -e @plugins/"$PLUGIN"
arch-chroot /mnt ansible-playbook -vvv /root/Ch-aronte/main.yaml --tags repos -e @/root/Ch-aronte/plugins/"$PLUGIN"

if [[ "$add_pkg" != "n" && "$add_pkg" != "N" ]]; then
  arch-chroot /mnt ansible-playbook -vvv /root/Ch-aronte/main.yaml --tags pkgs -e @/root/Ch-aronte/plugins/"$PLUGIN"
fi

# Limpa os arquivos de instalação
rm -rf /mnt/root/Ch-aronte

genfstab -U /mnt >/mnt/etc/fstab

