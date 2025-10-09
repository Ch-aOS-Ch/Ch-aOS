touch respostas.env
BG='#50694e' # background (de 50694e26)
FG='#c4ffbb' # foreground (de c4ffbbf5)

# Paleta Padrão
COLOR_00='#50694e' # black         (de 50694e26)
COLOR_01='#9d4131' # red           (de 9d41318e)
COLOR_02='#65d060' # green         (de 65d0606a)
COLOR_03='#d0cf60' # yellow        (de d0cf6068)
COLOR_04='#60d0cc' # blue          (de 60d0ccf7)
COLOR_05='#a560d0' # magenta       (de a560d0f7)
COLOR_06='#60d0bf' # cyan          (de 60d0bfff)
COLOR_07='#c7f0c9' # white         (de c7f0c9d6)

# Paleta Brilhante
COLOR_08='#171a17' # bright black  (de 171a1768)
COLOR_09='#cc1717' # bright red    (de cc17178e)
COLOR_10='#3ccc17' # bright green  (de 3ccc176a)
COLOR_11='#c8d200' # bright yellow (de c8d20068)
COLOR_12='#0048d2' # bright blue   (de 0048d2f7)
COLOR_13='#8900d2' # bright magenta(de 8900d2f7)
COLOR_14='#00d2a6' # bright cyan   (de 00d2a6ff)
COLOR_15='#c4ffbb' # bright white  (de c4ffbbf5)

echo -en "\e]11;${BG}\a"
echo -en "\e]10;${FG}\a"

echo -en "\e]4;0;${COLOR_00}\a"
echo -en "\e]4;1;${COLOR_01}\a"
echo -en "\e]4;2;${COLOR_02}\a"
echo -en "\e]4;3;${COLOR_03}\a"
echo -en "\e]4;4;${COLOR_04}\a"
echo -en "\e]4;5;${COLOR_05}\a"
echo -en "\e]4;6;${COLOR_06}\a"
echo -en "\e]4;7;${COLOR_07}\a"
echo -en "\e]4;8;${COLOR_08}\a"
echo -en "\e]4;9;${COLOR_09}\a"
echo -en "\e]4;10;${COLOR_10}\a"
echo -en "\e]4;11;${COLOR_11}\a"
echo -en "\e]4;12;${COLOR_12}\a"
echo -en "\e]4;13;${COLOR_13}\a"
echo -en "\e]4;14;${COLOR_14}\a"
echo -en "\e]4;15;${COLOR_15}\a"

echo -en "\e[0m"
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
