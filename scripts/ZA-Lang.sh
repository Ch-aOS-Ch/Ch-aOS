touch respostas.env
echo "Choose your language / Escolha sua linguagem:"
read -p "1- English / 2- Português: " -r lang
while [[ "$lang" != "1" && "$lang" != "2" ]]; do
  if [[ "$lang" == "1" ]]; then
    echo "You chose English"
    LANG="English"
    break
  elif [[ "$lang" == "2" ]]; then
    echo "Você escolheu Português"
    LANG="Portugues"
    break
  else
    echo "Por favor, escolha uma opção válida / Please choose a valid option."
    read -p "1- English / 2- Português: " -r lang
  fi
done

echo "$LANG" >>respostas.env
