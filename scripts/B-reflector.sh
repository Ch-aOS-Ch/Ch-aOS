#!/bin/bash
set -e
set -a
source respostas.env
set +a

# ==============================================================================
# SETUP DE IDIOMA E VARIÁVEIS
# ==============================================================================
case "$LANGC" in
"Portugues")
  MSG_ALMOST_FORGOT="Opa, quase que eu me esqueci de rodar o reflector, pera ae, vai ser 2 tempo"
  MSG_TYPING_SOUNDS="[sons de teclado]"
  MSG_INSTALLING="Ai ai... não temos o reflector, deixa que eu instalo rapidão"
  MSG_COMMAND_IS="jesus amado, que comando grande... aliás, é esse aqui:"
  # Define os países para o reflector. BR + US é uma ótima escolha.
  REFLECTOR_COUNTRIES="-c br -c us"
  FINALIZESC="Prontin, tá no grau."
  ;;
"English")
  MSG_ALMOST_FORGOT="Oh, I almost forgot to run reflector, hold on, it will be quick"
  MSG_TYPING_SOUNDS="[typing sounds]"
  MSG_INSTALLING="Oh no... reflector is not installed, let me install it real quick"
  MSG_COMMAND_IS="Damn, that's a long command... here it is:"
  # Define os países para o reflector. O usuário pode querer mudar 'eu' para seu país.
  REFLECTOR_COUNTRIES="-c eu -c us"
  FINALIZESC="Fuck yeah, thats finally done"
  ;;
*)
  echo "Unsupported language setting."
  exit 1
  ;;
esac

# ==============================================================================
# FLUXO PRINCIPAL DO SCRIPT
# ==============================================================================

sleep 1
echo "///...///"
sleep 1
echo "$MSG_ALMOST_FORGOT"
sleep 1
echo "$MSG_TYPING_SOUNDS"
sleep 1

# 1. Verifica se o reflector existe
if ! command -v reflector &>/dev/null; then
  echo "$MSG_INSTALLING"
  # 2. Se não existir, instala da forma mais segura (sincroniza E atualiza)
  pacman -Syu --noconfirm reflector
fi

# 3. Constrói e exibe o comando final que será executado
REFLECTOR_CMD="reflector $REFLECTOR_COUNTRIES --verbose --latest 25 --sort rate --save /etc/pacman.d/mirrorlist"
echo "$MSG_COMMAND_IS"
sleep 0.4
echo "$REFLECTOR_CMD"

# 4. Executa o comando
$REFLECTOR_CMD
sleep 1

echo "$FINALIZESC"
