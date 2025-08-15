echo "chose your language / Escolha sua linguagem:"
read -p "1- English / 2- Português: " -r lang
if [[ $lang == 1 ]]; then
  echo "You chose English"
  LANG=English
elif [[ $lang == 2 ]]; then
  echo "Você escolheu Português"
  LANG=Portugues
fi

while [[ -z "$lang" || ! "$lang" =~ ^(1|2)$ ]]; do
  echo "Por favor, escolha uma opção válida./please choose a valid option."
  read -p "1- English / 2- Português: " -r lang
  if [[ $lang == 1 ]]; then
    echo "You chose English"
    LANG=English
  elif [[ $lang == 2 ]]; then
    echo "Você escolheu Português"
    LANG=Portugues
  fi
done

echo "$lang" >>respostas.env
