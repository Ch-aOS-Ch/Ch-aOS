#!/bin/bash
pacotes=()
source ./scripts/resources.sh

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
read -p "quer mais algum pacote? (Y/n) " ok
set_env_var "PLUGIN_ACCEPT" "$ok"

if [[ "$ok" == "Y" || "$ok" == "y" || "$ok" == "" ]]; then
  echo "Ok, vamos adicionar mais pacotes!"
  # SISTEMA DE INICIALIZAÇÃO DE PLUGIN CUSTOM PARA ESSA INSTALAÇÃO
  plugin_dir="../sistema/vars/"
  qtd=$(find "$plugin_dir" -maxdepth 1 -type f -name 'custom*.yml' | wc -l)
  qtd=$((qtd + 1))
  mkdir -p "$plugin_dir"
  arquivo="${plugin_dir}/custom${qtd}.yml"
  set_env_var "PLUGIN" "$arquivo"
  echo "pacotes:" >>"$arquivo"
else
  echo "Ok, vamos continuar sem mais pacotes adicionais."
fi

while [[ "$ok" == "Y" || "$ok" == "y" || "$ok" == "" ]]; do
  read -p "Digite o nome do pacote: " pacote
  while ! pacman -Ss "$pacote" >/dev/null 2>&1; do
    echo "Pacote não encontrado."
    echo "Digite novamente:"
    read -p "Digite o nome do pacote: " pacote
  done
  if [[ ! " ${pacotes[*]} " =~ " $pacote " ]]; then
    echo "Adicionando $pacote..."
    pacotes+=("$pacote")
    echo "  - $pacote" >>"$arquivo"

  else
    echo "pacote já selecionado"
  fi
  read -p "mais algum? (Y/n) " ok
done
echo ""
echo "Lista dos pacotes que você escolheu:"
printf '%s\n' "${pacotes[@]}"

ansible-playbook main.yaml --tags instalacao

chmod +x ./scripts/D-regiao.sh
bash ./scripts/D-regiao.sh
