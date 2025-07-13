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
while [[ "$ok" == "Y" || "$ok" == "y" || "$ok" == "" ]]; do
    read -p "Digite o nome do pacote: " pacote
        while ! pacman -Ss "$pacote" > /dev/null 2>&1; do
            echo "Pacote não encontrado."
            echo "Digite novamente:"
            read -p "Digite o nome do pacote: " pacote
        done
        echo "Adicionando $pacote..."
        pacotes+=("$pacote")
        echo "  - $pacote" >> ../vars/necessarios.yml
    read -p "mais algum? (Y/n) " ok
done
echo ""
echo "Lista dos pacotes que você escolheu:"
printf '%s\n' "${pacotes[@]}"
