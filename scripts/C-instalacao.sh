#!/bin/bash
set -e

source ./lib/ui.sh
source ./lib/plugin.sh
source ./scripts/resources.sh
set -a
source ./respostas.env
set +a

# --- FUNÇÕES ---
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
      if yq -e '.repos.third_party[] | select(.name == "cachyOS")' "Ch-obolos/$PLUGIN" >/dev/null; then
        echo "$MSG_ALREADY_SELECTED"
      else
        echo "$MSG_ADDING cachyos..."
        yq -iy '.repos.third_party += [{"name": "cachyOS", "distribution": "arch", "url": "https://mirror.cachyos.org/cachyos-repo.tar.xz"}]' "Ch-obolos/$PLUGIN"
      fi
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
yq -iy '.pacotes |= (select(.) // [])' "Ch-obolos/$PLUGIN"

add_pkg="n"
read -p "$MSG_WANT_MORE" -r add_pkg
while [[ "$add_pkg" != "n" && "$add_pkg" != "N" ]]; do
  read -p "$MSG_PKG_NAME" -r pacote
  while ! pacman -Ss "$pacote" >/dev/null 2>&1; do
    echo "$MSG_NOT_FOUND"
    read -p "$MSG_TRY_AGAIN" -r pacote
  done

  plugin_add_to_list_unique "pacotes" "$pacote"
  echo "$MSG_ADDING $pacote..."

  read -p "$MSG_ANY_MORE" -r add_pkg
done

plugin_set_value "repos.managed.core" "true"
repos_update

CHROOT_TAGS="fstab,repos"
if [[ "$add_pkg" != "n" && "$add_pkg" != "N" ]]; then
  export CHROOT_TAGS="$CHROOT_TAGS,pkgs"
fi
