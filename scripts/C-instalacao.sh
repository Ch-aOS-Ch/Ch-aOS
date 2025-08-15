#!/bin/bash
pacotes=()
source ./scripts/resources.sh
if [ -f "$LANG"==Portugues ]; then
  echo "Beleza, mirrors atualizados. Bora continuar..."
  echo ""
  echo "Ok, agora vou te mostrar os pacotes essenciais que serão instalados no seu sistema base:"
  sleep 1
  echo "---------------------------------------------------"
  echo "Pacotes necessários:"
  echo "  - base"
  echo "  - base-devel"
  echo "  - linux"
  echo "  - linux-firmware"
  echo "  - linux-headers"
  echo "  - reflector"
  echo "  - refind"
  echo "  - nano"
  echo "  - networkmanager"
  echo "  - openssh"
  echo "---------------------------------------------------"
  sleep 1
  read -p "quer mais algum pacote? (Y/n) " -r ok
  set_env_var "PLUGIN_ACCEPT" "$ok"

  if [[ "$ok" == "Y" || "$ok" == "y" || "$ok" == "" ]]; then
    echo "Ok, vamos adicionar mais pacotes!"

    # SISTEMA DE INICIALIZAÇÃO DE PLUGIN CUSTOM PARA ESSA INSTALAÇÃO
    plugin_dir="./roles/sistema/vars/"
    qtd=$(find "$plugin_dir" -maxdepth 1 -type f -name 'custom*.yml' | wc -l)
    qtd=$((qtd + 1))
    mkdir -p "$plugin_dir"
    arquivo="${plugin_dir}custom${qtd}.yml"
    set_env_var "PLUGIN" "$arquivo"
    echo "pacotes:" >>"$arquivo"
  else
    echo "Ok, vamos continuar sem mais pacotes adicionais."
  fi

  while [[ "$ok" == "Y" || "$ok" == "y" || "$ok" == "" ]]; do
    read -p "Digite o nome do pacote: " -r pacote
    while ! pacman -Ss "$pacote" >/dev/null 2>&1; do
      echo "Pacote não encontrado."
      echo "Digite novamente:"
      read -p "Digite o nome do pacote: " -r pacote
    done
    if [[ ! "${pacotes[*]}" =~ $pacote ]]; then
      echo "Adicionando $pacote..."
      pacotes+=("$pacote")
      echo "  - $pacote" >>"$arquivo"
    else
      echo "pacote já selecionado"
    fi
    read -p "mais algum? (Y/n) " -r ok
  done
  echo ""
  echo "Lista dos pacotes que você escolheu:"
  printf '%s\n' "${pacotes[@]}"

  ansible-playbook -vvv ./main.yaml --tags instalacao
  genfstab -U /mnt >>/mnt/etc/fstab
elif [ -f "$LANG"==English ]; then
  echo "Alright, mirrors updated. Let's continue..."
  echo ""
  echo "Now I'll show you the essential packages that will be installed on your base system:"
  sleep 1
  echo "---------------------------------------------------"
  echo "Required packages:"
  echo "  - base"
  echo "  - base-devel"
  echo "  - linux"
  echo "  - linux-firmware"
  echo "  - linux-headers"
  echo "  - reflector"
  echo "  - refind"
  echo "  - nano"
  echo "  - networkmanager"
  echo "  - openssh"
  echo "---------------------------------------------------"
  sleep 1
  read -p "Do you want to add more packages? (Y/n) " -r ok
  set_env_var "PLUGIN_ACCEPT" "$ok"
  if [[ "$ok" == "Y" || "$ok" == "y" || "$ok" == "" ]]; then
    echo "Okay, let's add more packages!"

    # CUSTOM PLUGIN INITIALIZATION SYSTEM FOR THIS INSTALLATION
    plugin_dir="./roles/sistema/vars/"
    qtd=$(find "$plugin_dir" -maxdepth 1 -type f -name 'custom*.yml' | wc -l)
    qtd=$((qtd + 1))
    mkdir -p "$plugin_dir"
    arquivo="${plugin_dir}custom${qtd}.yml"
    set_env_var "PLUGIN" "$arquivo"
    echo "pacotes:" >>"$arquivo"
  else
    echo "Okay, let's continue without additional packages."
  fi
  while [[ "$ok" == "Y" || "$ok" == "y" || "$ok" == "" ]]; do
    read -p "Enter the package name: " -r pacote
    while ! pacman -Ss "$pacote" >/dev/null 2>&1; do
      echo "Package not found."
      echo "Please enter again:"
      read -p "Enter the package name: " -r pacote
    done
    if [[ ! "${pacotes[*]}" =~ $pacote ]]; then
      echo "Adding $pacote..."
      pacotes+=("$pacote")
      echo "  - $pacote" >>"$arquivo"
    else
      echo "Package already selected."
    fi
    read -p "Any more? (Y/n) " -r ok
  done
  echo ""
  echo "List of packages you chose:"
  printf '%s\n' "${pacotes[@]}"
  ansible-playbook -vvv ./main.yaml --tags instalacao
  genfstab -U /mnt >>/mnt/etc/fstab
else
  echo "Unsupported language setting."
  bash scripts/C-instalacao.sh
  exit 1
fi
