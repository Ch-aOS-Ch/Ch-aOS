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
  MSG_SYSTEM_INSTALLED="tá, teu sistema tá instalado, agora bora pra parte legal"
  MSG_FIX_CLOCK="primeiro, vamos usar ln -sf /usr/share/zoneinfo/(sua região) pra consertar esse relógio..."
  MSG_SEARCH_REGION="pesquisa aí a região de timedatectl mais próxima de você (ou não escreva nada pra deixar em SP)"
  MSG_REGION_PROMPT="Região: "
  DEFAULT_REGION="America/Sao_Paulo"
  MSG_INVALID_REGION="Região inválida! tente de novo "
  MSG_SYNCING_CLOCK="syncando o relógio com hwclock --systohc..."
  MSG_CLOCK_SYNCED="relógio sincronizado paizão/mãezona/patrono... eu tenho que parar de usar tanto pronome assim, vou enlouquecer"
  MSG_LOCALE_INTRO="oooookay, bora pro teu locale (tua linguagem), vamo usar nano /etc/locale.gen e VOCÊ (sim, VOCÊ) vai descomentar a linha do locale que tu quiser"
  MSG_LOCALE_GEN_INFO="ah, e deixa que eu rodo o locale-gen pra você"
  MSG_ALL_SET_PROMPT="tudo certo? (Y/n) "
  MSG_READ_AGAIN="Por favor, leia as instruções novamente."
  MSG_TELL_ME_LOCALE="agora, me diga a linha que tu descomentou, só coloca a região, tipo 'pt_BR' ou 'en_US' e SIM, preciso das duas letras maíusculas no final. "
  MSG_LOCALE_NOT_FOUND="Locale não encontrado no locale.gen"
  MSG_TRY_AGAIN_LOCALE="Tenta de novo, com algo tipo pt_BR ou en_US: "
  KEYMAP_VALUE="br-abnt2"
  ;;
"English")
  MSG_SYSTEM_INSTALLED="Alright, your system is installed, now let's get to the fun part"
  MSG_FIX_CLOCK="First, we'll use ln -sf /usr/share/zoneinfo/(your region) to fix the clock..."
  MSG_SEARCH_REGION="Search for the closest timedatectl region to you (or leave it blank to set it to NY)"
  MSG_REGION_PROMPT="Region: "
  DEFAULT_REGION="America/New_York"
  MSG_INVALID_REGION="Invalid region! Please try again."
  MSG_SYNCING_CLOCK="Syncing the clock with hwclock --systohc..."
  MSG_CLOCK_SYNCED="Clock synced, sir/miss/gentleperson... I really need to stop using so many pronouns, it's driving me crazy"
  MSG_LOCALE_INTRO="Okay, let's set your locale (language), open nano /etc/locale.gen and YOU (yes, YOU) will uncomment the line for the locale you want"
  MSG_LOCALE_GEN_INFO="Oh, and I'll run locale-gen for you"
  MSG_ALL_SET_PROMPT="All set? (Y/n) "
  MSG_READ_AGAIN="Please read the instructions again."
  MSG_TELL_ME_LOCALE="Now, tell me the line you uncommented, just type the region, like 'en_US' or 'pt_BR', and YES, I need those two uppercase letters at the end. "
  MSG_LOCALE_NOT_FOUND="Locale not found in locale.gen"
  MSG_TRY_AGAIN_LOCALE="Try again, with something like en_US or pt_BR: "
  KEYMAP_VALUE="us"
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
echo "$MSG_SYSTEM_INSTALLED"

# --- TIMEZONE ---
echo "$MSG_FIX_CLOCK"
sleep 1
echo "$MSG_SEARCH_REGION"
read -p "$MSG_REGION_PROMPT" -r region

if [ -z "$region" ]; then
  region="$DEFAULT_REGION"
fi

while [ ! -f "/usr/share/zoneinfo/$region" ]; do
  echo "$MSG_INVALID_REGION"
  read -p "$MSG_REGION_PROMPT" -r region
done

ln -sf "/usr/share/zoneinfo/$region" "/mnt/etc/localtime"
echo "$MSG_SYNCING_CLOCK"
sleep 1
arch-chroot /mnt hwclock --systohc
echo "$MSG_CLOCK_SYNCED"
sleep 1

# --- LOCALE ---
echo "$MSG_LOCALE_INTRO"
sleep 1
echo "$MSG_LOCALE_GEN_INFO"

read -p "$MSG_ALL_SET_PROMPT" -r certo
# Usando a lógica de confirmação corrigida
while ! [[ "$certo" == "Y" || "$certo" == "y" || "$certo" == "" ]]; do
  echo "$MSG_READ_AGAIN"
  read -p "$MSG_ALL_SET_PROMPT" -r certo
done

sleep 1
nano /mnt/etc/locale.gen
sleep 1
arch-chroot /mnt locale-gen

read -p "$MSG_TELL_ME_LOCALE" -r lingua
while ! grep -q "^#\?$lingua.UTF-8" /mnt/etc/locale.gen; do
  echo "$MSG_LOCALE_NOT_FOUND"
  read -p "$MSG_TRY_AGAIN_LOCALE" -r lingua
done

echo "LANG=$lingua.UTF-8" >/mnt/etc/locale.conf
echo "KEYMAP=$KEYMAP_VALUE" >/mnt/etc/vconsole.conf

echo "Locale e keymap configurados!"
sleep 1
