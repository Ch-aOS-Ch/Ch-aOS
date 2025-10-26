#!/bin/bash

echo "respostas.env" >>.gitignore && touch respostas.env
echo -en "\e]P0152212" # black (background)
echo -en "\e]P19d4131" # red
echo -en "\e]P265d060" # green
echo -en "\e]P3d0cf60" # yellow
echo -en "\e]P460d0cc" # blue
echo -en "\e]P5a560d0" # magenta
echo -en "\e]P660d0bf" # cyan
echo -en "\e]P7c7f0c9" # white
echo -en "\e]P8171a17" # bright black
echo -en "\e]P9cc1717" # bright red
echo -en "\e]PA3ccc17" # bright green
echo -en "\e]PBc8d200" # bright yellow
echo -en "\e]PC0048d2" # bright blue
echo -en "\e]PD8900d2" # bright magenta
echo -en "\e]PE00d2a6" # bright cyan
echo -en "\e]PFc4ffbb" # bright white (foreground)

# Set default foreground and background
echo -en "\033[0m"

clear

echo "Choose your language / Escolha sua linguagem:"

while true; do
  read -p "1- English / 2- Português: " -r lang
  if [[ "$lang" == "1" ]]; then
    echo "You chose English"
    export LANGC="English"
    break
  elif [[ "$lang" == "2" ]]; then
    echo "Você escolheu Português"
    export LANGC="Portugues"
    break
  else
    echo "Por favor, escolha uma opção válida / Please choose a valid option."
  fi
done

echo "LANGC=$LANGC" >respostas.env
set -a
source respostas.env
set +a
