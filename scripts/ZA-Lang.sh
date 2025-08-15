echo "Choose your language / Escolha sua linguagem:"
while true; do
  read -p "1- English / 2- Português: " -r lang
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
  fi
done

echo "$LANG" >>respostas.env
