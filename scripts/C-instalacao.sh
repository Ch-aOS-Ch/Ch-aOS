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

  # Inicializa a estrutura no YAML para evitar erros
  yq -iy '.repos.managed.extras |= (select(.) // false)' "plugins/$PLUGIN"
  yq -iy '.repos.third_party |= (select(.) // [])' "plugins/$PLUGIN"

  want_repo="y"
  while [[ "$want_repo" =~ ^[Yy]?$ ]]; do
    read -p "$MSG_WHICH_REPO" -r repo
    local repo_name
    repo_name=$(echo "$repo" | tr '[:upper:]' '[:lower:]')

    case $repo_name in
    "multilib" | "extra")
      echo "$MSG_ADDING $repo_name..."
      yq -iy '.repos.managed.extras = true' "plugins/$PLUGIN"
      ;;
    "cachyos" | "cachy")
      if yq -e '.repos.third_party[] | select(.name == "cachyOS")' "plugins/$PLUGIN" >/dev/null; then
        echo "$MSG_ALREADY_SELECTED"
      else
        echo "$MSG_ADDING cachyos..."
        yq -iy '.repos.third_party += [{"name": "cachyOS", "distribution": "arch", "url": "https://mirror.cachyos.org/cachyos-repo.tar.xz"}]' "plugins/$PLUGIN"
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

yq -iy '.repos.managed.core = true' "plugins/$PLUGIN"
repos_update

set -a
source respostas.env
set +a

# Copia o projeto para dentro do chroot para que o Ansible possa ser executado lá
cp -r ./ /mnt/root/Ch-aronte/

# Executa os playbooks em sequência, a maioria DENTRO do chroot
ansible-playbook -vvv ./main.yaml --tags instalacao -e @plugins/"$PLUGIN"

# Executa as roles restantes de dentro do chroot com uma única chamada
CHROOT_TAGS="fstab,bootloader,repos"
if [[ "$add_pkg" != "n" && "$add_pkg" != "N" ]]; then
  CHROOT_TAGS="$CHROOT_TAGS,pkgs"
fi
arch-chroot /mnt ansible-playbook -vvv /root/Ch-aronte/main.yaml --tags "$CHROOT_TAGS" -e @/root/Ch-aronte/plugins/"$PLUGIN"

# Limpa os arquivos de instalação
rm -rf /mnt/root/Ch-aronte
