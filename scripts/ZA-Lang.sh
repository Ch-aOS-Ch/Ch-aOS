touch respostas.env
echo "Choose your language / Escolha sua linguagem:"
read -p "1- English / 2- Português: " -r lang
while [[ "$lang" != "1" || "$lang" != "2" ]]; do
  if [[ "$lang" == "1" ]]; then
    echo "You chose English"
    LANGC="English"
    break
  elif [[ "$lang" == "2" ]]; then
    echo "Você escolheu Português"
    LANGC="Portugues"
    break
  else
    echo "Por favor, escolha uma opção válida / Please choose a valid option."
    read -p "1- English / 2- Português: " -r lang
  fi
done

echo "$LANGC" >>respostas.env
set -a
source respostas.env
set +a
