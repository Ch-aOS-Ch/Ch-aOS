echo "chose your language / Escolha sua linguagem:"
read -p "1- English / 2- Português: " -r lang
if [[ $lang == 1 ]]; then
  echo "You chose English"
  LANG=English
elif [[ $lang == 2 ]]; then
  echo "Você escolheu Português"
  LANG=Português
else
  echo "Invalid option / Opção inválida"
  source scripts/ZA-Lang.sh
fi

echo "$lang" >>respostas.env
