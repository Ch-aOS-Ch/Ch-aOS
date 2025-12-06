[english version](./README.md)
***Suíte de projetos Ch-aOS***

[![Status do Projeto: Ativo](https://img.shields.io/badge/status-ativo-success.svg)](https://github.com/Dexmachi/Ch-aronte)

***Ch-aronte para Arch; Ch-imera para NixOS; Ch-obolos para todos. Estudando a viabilidade de um Ch-iron para Fedora e um Ch-ronos para Debian.***

## Do que se trata?

- O Ch-aOS foi projetado para ser uma forma de gerenciar seu sistema Linux de maneira declarativa e modular, desde a instalação até a configuração pós-instalação.

## Como funciona?

- A CLI chaos usa Python, Pyinfra e OmegaConf como seu motor principal, permitindo uma abordagem de paradigma declarativo de forma mais simples.
- O Ch-aronte é apenas um módulo plugável que fornece os "roles" (funções) para a chaos, um backend plugável feito para sistemas Arch Linux.
- O Ch-imera será um pouco diferente, ele irá _transpilar_ os arquivos Ch-obolos em expressões Nix simples, permitindo um _kickstart_ em sistemas NixOS, basicamente deixando você "testar" o paradigma declarativo sem precisar aprendê-lo dentro de um sistema "puramente declarativo".
- O Ch-obolo é o sistema de configuração principal, projetado para ser uma configuração universal para todos os projetos Ch-aOS, permitindo que você troque de distro com facilidade.

## Você disse plugins??
- Sim! A CLI chaos é basicamente apenas a própria CLI, sem nenhum backend. Os backends são os próprios plugins, o que significa que você pode criar seu próprio backend para sua própria distro, se quiser!
- Alguns exemplos de backends possíveis são encontrados na pasta `external_plugins`, incluindo um backend mock para testes e um backend `chaos-dots` para gerenciamento de dotfiles! (Este eu mesmo uso!)

### Mas e quanto a... você sabe... gerenciar meu _sistema_ de verdade??
- É aí que entram os "cores". Cores são apenas plugins pré-fabricados que gerenciam distros específicas, como o Ch-aronte para Arch Linux!
- Estes são feitos por mim, euzinho e eu mesmo, mas qualquer um pode criar seu próprio core se quiser... porque, você sabe... são plugins.
- Os Cores devem conter todo o mínimo necessário para gerenciar um sistema, como gerenciamento de pacotes, usuários, serviços, etc.

## Começando

1. Clone este repositório (estou trabalhando para torná-lo instalável via pip/aur, mas por enquanto, esta é a única maneira de obtê-lo).
2. Vá para `./cli/build/b-coin/` e execute `makepkg -fcsi` para instalar a CLI chaos.
3. (Opcional) vá para `../../Ch-aronte/build/core` e execute `makepkg -fcsi` para instalar o core Ch-aronte.
4. (Opcional) vá para `../../external_plugins/chaos-dots` e execute `makepkg -fcsi` para instalar o plugin chaos-dots.
5. Agora você pode executar `chaos -h` para ver o menu de ajuda e `chaos -r` para verificar todos os roles disponíveis!
> [!TIP]
>
> O uso de `sops` é altamente recomendado. Ele é usado para gerenciamento de segredos. No momento, não é uma dependência obrigatória, mas algumas funcionalidades não funcionarão sem ele e seu não uso será descontinuado no futuro.

## O Sistema Ch-obolos

> [!TIP]
>
> Você pode usar `chaos --set-chobolo`, `--set-sec-file` e `--set-sops-file` para definir seu arquivo Ch-obolo base, arquivo de segredos ou arquivo de configuração sops. Isso será usado como base para todas as execuções de roles e decriptações!

### Exemplo de um arquivo Ch-obolos para o Ch-aronte:
```YAML
# Define usuários do sistema, grupos e hostname
users:
  - name: "dexmachina"
    shell: "zsh"
    sudo: True
    groups:
      - wheel
      - dexmachina
hostname: "Dionysus"

secrets:
  sec_mode: sops
  sec_file: /caminho/absoluto/para/Ch-obolos/secrets-here.yml # <~ Não é necessário se você já configurou com a CLI chaos, mas pode ser usado como fallback!
  sec_sops: /caminho/absoluto/para/Ch-obolos/sops-secs.yml # <~ Não é necessário se você já configurou com a CLI chaos, mas pode ser usado como fallback!

packages:
  - neovim
  - fish
  - starship
  - btop

aurPackages: # <~ sim, eu os separei, isso é uma rede de segurança para quando você NÃO tem um maldito aur helper (como ousa?)
  - 1password-cli
  - aurroamer # <~ Recomendo fortemente, pacote muito bom
  - aurutils
  - bibata-cursor-theme-bin
 
bootloader: "grub" # ou "refind"

# baseOverride:  <~ muito perigoso, permite que você altere os pacotes base do sistema (ex: linux linux-firmware ansible ~~cowsay~~ etc)
#   - linux-cachyos-headers
#   - linux-cachyos
#   - linux-firmware

aurHelpers:
  - yay
  - paru

mirrors:
  countries:
    - "br"
    - "us"
  count: 25

# Gerencia serviços do systemd
services:
  - name: NetworkManager
    running: True # <~ o padrão é True
    on_boot: true # <~ como o padrão é True
                  # eu gosto de manter isso para maior granularidade
    dense_service: true # <~ isso diz ao script para usar regex para encontrar todos os serviços com "NetworkManager" no nome

  - name: bluetooth
    dense_service: true # <~ Porque eu não quero colocar .service toda vez

  - name: sshd # <~ coloca .service automaticamente lmao

  - name: nvidia
    dense_service: true

  - name: sddm.service

# Gerencia repositórios do pacman
repos:
  managed:
    core: True      # Habilita o repositório [core] (padrão: true)
    extras: true    # Habilita o repositório [extras+multilib] (padrão: false)
    unstable: false # Desabilita os repositórios [testing] (padrão: false)
  third_party:
    - name: "cachyOS" # <~ você pode adicionar quantos repositórios de terceiros quiser, desde que os tenha instalados
      include: /etc/pacman.d/cachyos-mirrorlist
      distribution: "arch"

# Gerencia dotfiles de repositórios git
dotfiles:
  - url: https://github.com/seu-usuario/seus-dotfiles.git
    user: dexmachina # <~ usuário onde os dotfiles serão aplicados
    branch: main # <~ opcional, o padrão é main
    pull: true # <~ opcional, o padrão é false. Se true, ele puxará as últimas alterações
    links:
      - from: "zsh" # <~ esta é uma _pasta_ dentro do meu repositório de dotfiles
        to: . # <~ o padrão é ., ele usa o diretório home do usuário declarado como ponto de partida.
        open: true # <~ define se o script deve criar um link simbólico para os arquivos _dentro_ da pasta _ou_ para a própria pasta. (padrão: false)
      - from: "bash"
        open: true
      - from: ".config"
# ATENÇÃO: _TODOS_ OS ARQUIVOS QUE VOCÊ COLOCAR AQUI _E_ JÁ EXISTIREM SERÃO MOVIDOS PARA UM ARQUIVO DE BACKUP. SE VOCÊ _REMOVER_ UM ARQUIVO DA LISTA, ELE TAMBÉM SERÁ REMOVIDO DO CAMINHO QUE VOCÊ DEFINIU. (óbvio, é declarativo)

# Define partições de disco (geralmente preenchido pelo script interativo)
partitioning: # <~ não é e nunca será traduzível para um configurations.nix :( mas é traduzível para um disko.nix :)
  disk: "/dev/sdb" # <~ em qual disco você deseja particionar
  partitions:
    - name: chronos # <~ O Ch-aronte usa labels para o fstab e outras coisas, isso não muda nada na sua experiência geral, mas é uma comodidade para mim
      important: boot # <~ Apenas 4 tipos: boot, root, swap e home. É usado para definir como o role deve tratar a partição (principalmente boot e swap)
      size: 1GB # <~ Use G. MiB pode funcionar, mas talvez não, ainda não está bem estabilizado
      mountpoint: "/boot" # <~ obrigatório (dã)
      part: 1 # <~ isso informa qual é a partição (sdb1,2,3,4...)
      type: vfat # <~ ou ext4, btrfs, bem, você entendeu

    - name: Moira
      important: swap
      size: 4GB
      part: 2
      type: linux-swap

    - name: dionysus_root
      important: root
      size: 46GB
      mountpoint: "/"
      part: 3
      type: ext4

    - name: dionysus_home
      important: home
      size: 100%
      mountpoint: "/home"
      part: 4
      type: ext4

# Define configurações de região, idioma e teclado
region:
  timezone: "America/Sao_Paulo"
  locale:
    - "pt_BR.UTF-8"
    - "en_US.UTF-8"
  keymap: "br-abnt2"

```
> [!WARNING]
>
> Você pode encontrar um exemplo mais completo em [Meus-Ch-obolos](Ch-obolos/dex/dex-migrating.yml), estes são os Ch-obolos que eu uso ativamente para gerenciar meu próprio sistema!

# Exemplo de uso:
![chaos usage](./imagens/B-coin-test.gif)

## Roadmap do Projeto

- [-] = Em Progresso, provavelmente em outro branch, seja sendo trabalhado ou já implementado, mas não totalmente testado.

### MVP
- [-] Instalador Mínimo com Detecção de Firmware
- [x] Sistema de Plugins para o Ch-aronte

### Modularidade + Automação
- [x] Gerenciador de Dotfiles integrado ao Sistema de Plugins
- [x] CLI helper para gerenciamento de sistema chaos.

### Declaratividade
- [-] Modo de instalação totalmente declarativo, com sua única necessidade sendo o arquivo *.yml para o Ch-aronte.
- [x] Configuração de sistema pós-instalação totalmente declarativa com apenas um arquivo custom*.yml para o Ch-aronte.
- [x] Gerenciador de estado de pacotes declarativo (Instala e desinstala declarativamente) para o Ch-aronte.
- [x] Gerenciador de repositórios para o Ch-aronte.

### Qualidade + segurança
- [-] Testes Pytest + flake8 para toda a base de código.

### Ideias em estudo
- [-] Gerenciamento de segredos (ALTAMENTE expansível, atualmente usado apenas para senhas de usuário).
  - Agora que finalmente integrei o [sops](https://github.com/getsops/sops) ao sistema, posso facilmente gerenciar segredos com criptografia e commits seguros.

## Contribuindo

Contribuições são muito bem-vindas. Se você tem ideias para melhorar o Ch-aronte, sua ajuda é muito bem-vinda! Confira o `CONTRIBUTING.md` para começar.

Áreas de interesse particular incluem:

- Traduções criativas e melhorias no estilo narrativo.
- Sugestões e implementações para configurações pós-instalação.
- Ajuda para verificar se os Ch-obolos são verdadeiramente declarativos ou não.
- Criação de issues.

## Agradecimentos

A inspiração principal para este projeto veio do [archible](https://github.com/0xzer0x/archible) de [0xzer0x](https://github.com/0xzer0x).
> Se você está lendo isso (duvido, mas vai que), muito obrigado por sua ferramenta incrível, espero um dia alcançar o nível de criatividade e expertise que você teve para torná-la realidade.