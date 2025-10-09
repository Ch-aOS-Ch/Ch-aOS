touch respostas.env
echo -en "\e]50694e26" # black (background)
echo -en "\e]9d41318e" # red
echo -en "\e]65d0606a" # green
echo -en "\e]d0cf6068" # yellow
echo -en "\e]60d0ccf7" # blue
echo -en "\e]a560d0f7" # magenta
echo -en "\e]60d0bfff" # cyan
echo -en "\e]c7f0c9d6" # white
echo -en "\e]171a1768" # bright black
echo -en "\e]cc17178e" # bright red
echo -en "\e]3ccc176a" # bright green
echo -en "\e]c8d20068" # bright yellow
echo -en "\e]0048d2f7" # bright blue
echo -en "\e]8900d2f7" # bright magenta
echo -en "\e]00d2a6ff" # bright cyan
echo -en "\e]c4ffbbf5" # bright white (foreground)

# Set default foreground and background
echo -en "\033[0m"

echo "Choose your language / Escolha sua linguagem:"

while true; do
  read -p "1- English / 2- Português: " -r lang
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
  fi
done

echo "LANGC=$LANGC" >respostas.env
set -a
source respostas.env
set +a
