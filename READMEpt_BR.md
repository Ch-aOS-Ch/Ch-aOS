[english version](./README.md)
# Ch-aronte

**Seu guia pelo submundo do Arch Linux.**

[![Status do Projeto: Ativo](https://img.shields.io/badge/status-ativo-success.svg)](https://github.com/Dexmachi/Ch-aronte)

---

**Ch-aronte** não é apenas um instalador. É uma jornada guiada e interativa pelo coração do Arch Linux, projetada para quem deseja instalar com confiança e aprender o processo de verdade — sem mais copiar e colar comandos cegamente.

Construído com a robustez do **Ansible** e a interatividade do **Shell Script**, ele automatiza as partes tediosas e te entrega o controle onde importa, transformando uma instalação complexa em uma experiência declarativa.

***PARTE DA SUÍTE DE PROJETOS Ch-aOS (Ch-aronte + Ch-imera for nix + Ch-obolos)***

## Por que "Ch-aronte"?

1. O nome: Bem, primeiro de tudo, Charon (Caronte) é o barqueiro do submundo na mitologia grega, guiando as almas através do rio Estige. Ch-aronte é um trocadilho, combinando "Charon" com "Chroot" + eu sou brasileiro, então o nome "Charon" foi "aportuguesado".
2. As partes: Caronte, o barqueiro, também recebia 2 moedas para guiar as almas, e o Arch tem 2 partes para configurar (a instalação e a pós-instalação), então este script também terá 2 partes, uma para instalar o Arch e outra para gerenciar seu sistema (A-coin.sh e o helper B-coin, respectivamente), ambas de forma declarativa.
3. Mas por que usar o Ch-aronte? Simples: ele segue a filosofia do Nix, ou seja, ele adiciona uma camada de abstração declarativa à sua configuração, permitindo que você, na linguagem do script, diga "crie estes usuários com estes grupos" ou "mantenha estes pacotes instalados, instale os que não estão e apague todo o resto (sim, perigoso, eu sei)", tudo do conforto da sua própria instalação Arch. Além disso, ele também funciona como um instalador declarativo, permitindo uma fácil reprodutibilidade do seu sistema.

## Funcionalidades Principais

* **Instalação Interativa e Guiada**: Um processo passo a passo que explica o que está acontecendo.
* **Detecção Automática de Firmware**: Instalação para **UEFI** ou **BIOS**.
* **Sistema de Plugins**: Adicione seus próprios pacotes e, no futuro, gerencie seus dotfiles com presets customizados, gerencie as configurações de sistema do Linux (como usuários, hostname, etc.), gerencie pacotes de forma declarativa e gerencie repositórios.
* **Código Aberto e Legível**: A base de código foi refatorada para servir como um exemplo prático e limpo de automação.

## A Arquitetura: Orquestrador + Executor

O projeto utiliza uma arquitetura híbrida poderosa e flexível:

* **Shell Script (O Orquestrador)**: Atua como a interface interativa, coletando a entrada do usuário, validando dados e orquestrando a sequência de instalação.
* **Ansible (O Executor)**: Atua no backend, executando as tarefas pesadas de forma declarativa e confiável — particionamento, instalação de pacotes e configuração do sistema.

## Começando

Projetado para ser executado diretamente do ambiente Live ISO do Arch Linux.

### Pré-requisitos:

* Uma conexão com a internet (use `iwctl` no ambiente live).
* Um Live ISO do Arch Linux em execução.

### Passos da Instalação:

```bash
# 1. No ambiente live, conecte-se à internet
iwctl

# 2. (Opcional, mas recomendado) Aumente o espaço em RAM para o liveboot
mount -o remount,size=2G /run/archiso/cowspace

# 3. Instale as dependências
pacman -Sy --noconfirm ansible git yq

# 4. Clone o repositório e inicie o instalador
git clone https://github.com/Dexmachi/Ch-aronte.git
cd Ch-aronte

# IMPORTANTE: Execute o script de dentro da pasta do projeto
chmod +x A-coin.sh
./A-coin.sh
```
> [!WARNING]
> O script é seu guia. Siga as instruções no terminal e deixe que o Ch-aronte te conduza pela instalação.

## Sistema de Plugins

Personalize sua instalação criando seus próprios presets de pacotes.
1. Crie um arquivo chamado custom-SEU-PLUGIN.yml dentro de ./Ch-obolos/.
2. Embora você possa colocar tudo em um único arquivo, recomendo separar as configurações em múltiplos arquivos e usar um arquivo principal para importá-los. Isso torna sua configuração mais limpa e reutilizável.

Por exemplo, você poderia ter a seguinte estrutura em seu diretório `./Ch-obolos/`:
```
.
├── custom-main.yml
├── dotfiles.yml
├── packages.yml
├── partitions.yml
├── region.yml
├── repos.yml
├── services.yml
└── users.yml
```

Seu arquivo principal, `custom-main.yml`, usaria então `imports` para combinar os outros arquivos. A chave `strategy` (`override`, `combine`, `merge`) determina como os dados são mesclados em caso de conflito de chaves.
```YAML
# ./Ch-obolos/custom-main.yml
# Este é o arquivo de ponto de entrada principal para o seu plugin.
plug_name: custom-main.yml # <- essêncial, isso identifica o plugin

imports:
  - file: 'users.yml'
    strategy: merge
    merge_keys:
      - users

  - file: 'packages.yml'
    strategy: override

  - file: 'services.yml'
    strategy: combine

  - file: 'repos.yml'
    strategy: combine

  - file: 'dotfiles.yml'
    strategy: merge
    merge_keys:
      - dotfiles

  # Partições e região são geralmente definidos pelo script interativo,
  # mas também podem ser importados se você estiver rodando em modo totalmente declarativo.
  - file: 'particoes.yml'
    strategy: override

  - file: 'region.yml'
    strategy: override
```

E os arquivos correspondentes conteriam as configurações específicas, por exemplo:
```YAML
# ./Ch-obolos/packages.yml
pacotes:
  - neovim
  - fish
  - starship
  - btop

bootloader: "grub"
```

Ou:
```YAML
# ./Ch-obolos/users.yml
users:
  - name: "dexmachina"
    shell: "/bin/zsh"
    groups:
      - wheel
      - dexmachina

  - name: "root"
    shell: "/bin/bash"
    groups:
      - root
hostname: "Dionysus"
wheel_access: true
secrets:
  sec_mode: "charonte" #<- depois vou adicionar um modo "system", que requer setup prévio do ansible-vault ou do sops do nix
  sec_file: "Ch-obolos/secrets.yml" #<- arquivo de segredos (senhas), deve ser secreto e é NECESSÁRIO para sec_mode "charonte"
```

### Exemplo de arquivo completo com tudo em um só:
```YAML
# É recomendado separar essas configurações em arquivos diferentes
# (ex: users.yml, packages.yml) e usar um arquivo de plugin principal para importá-los,
# mas para este exemplo, tudo está em um só lugar.

# Define os usuários do sistema, grupos e hostname
users:
  - name: "dexmachina"
    shell: "/bin/zsh"
    groups:
      - wheel
      - dexmachina
  - name: "root"
    shell: "/bin/bash"
    groups:
      - root
hostname: "Dionysus"
wheel_access: true # Concede acesso sudo ao grupo 'wheel'

# Define a lista de pacotes a ser gerenciada declarativamente
pacotes:
  - neovim
  - fish
  - starship
  - btop
bootloader: "grub" # ou "refind"

# Gerencia os serviços do systemd
services:
  - name: "NetworkManager"
    state: "started"
    enabled: true
  - name: "bluetooth"
    state: "started"
    enabled: true

# Gerencia os repositórios do pacman
repos:
  managed:
    extras: true      # Ativa o repositório [extras+multilib]
    unstable: false   # Desativa os repositórios [testing]
  third_party:
    - name: "cachyOS"
      distribution: "arch"
      url: "https://mirror.cachyos.org/cachyos-repo.tar.xz"

# Gerencia dotfiles a partir de repositórios git
dotfiles:
  - repo: https://github.com/seu-usuario/seus-dotfiles.git
    # Para decidir como o script irá se comportar, você tem 3 opções de como ele funcionará.
    install_command: "seu_comando_customizado_de_dotfile.sh"
    # OPÇÃO 1: install_command é uma variável que você pode definir para decidir como o script instalará seus dotfiles. Ele usa a raiz do seu repositório como ponto de partida, então esteja ciente disso.
    manager: "stow"
    # OPÇÃO 2: Você define um gerenciador e o script o aplica a todas as pastas em seu repositório.
    # OPÇÃO 3: deixar em branco (nem install_command nem manager) faz com que o script procure por um arquivo "install.sh" dentro da raiz do seu repositório, usando-o como base para instalar seus dotfiles.

# Define as partições de disco (geralmente preenchido pelo script interativo)
particoes:
  root:
    device: "/dev/sda2"
    label: "ARCH_ROOT"
    formato: "ext4"
  home:
    device: "/dev/sda4"
    label: "ARCH_HOME"
  boot:
    device: "/dev/sda1"
    label: "ESP"
  swap:
    device: "/dev/sda3"
    label: "SWAP"

# Define as configurações de região, idioma e teclado
region:
  timezone: "America/Sao_Paulo"
  locale:
    - "pt_BR.UTF-8"
    - "en_US.UTF-8"
  keymap: "br-abnt2"

```
> [!WARNING]
> USE ESPAÇOS EM VEZ DE TABS, O ANSIBLE É MUITO SENSÍVEL.

### Para gerar o plugin do seu sistema atual, rode:
```bash
cd Ch-aronte
DIR="./Ch-obolos/" && FILENAME="custom-meu-sistema-atual.yml" && mkdir -p "$DIR" && echo "pacotes:" > "$DIR/$FILENAME" && pacman -Qqen | sed 's/^/  - /' >> "$DIR/$FILENAME" && echo "Plugin gerado com sucesso em '$DIR/$FILENAME'!"
```
> [!INFO]
> Funciona diretamente do seu terminal!


## Roadmap do Projeto

- [-] = Em Progresso, provavelmente em outra branch, seja sendo trabalhado ou já implementado, mas não totalmente testado.

### MVP
- [x] Instalador Mínimo com Detecção de Firmware
- [x] Sistema de Plugins para Pacotes Customizados

### Modularidade + Automação
- [x] Gerenciador de Dotfiles integrado ao Sistema de Plugins

### Declaratividade + Rollback
- [-] Modo de instalação totalmente declarativo, com sua única necessidade sendo o arquivo custom*.yml. (Eu só preciso implementar o verificador no início do script e, se o arquivo de plugin existir e for selecionado, rodar em modo declarativo)
- [-] Configuração de sistema pós-instalação totalmente declarativa com apenas um arquivo custom*.yml. (Eu só preciso implementar o helper B-coin para este)
- [x] Gerenciador de estado de pacotes declarativo (Instala e desinstala declarativamente).
- [x] Gerenciador de repositórios.

### Qualidade + segurança
- [-] Testes com ansible-lint e ansible-test. (Atualmente sendo feito manualmente)

### Ideias em estudo
- [-] Gerenciamento de segredos (ALTAMENTE expansível, atualmente usado apenas para senhas de usuário).
- [ ] Suporte a ALA/ALHA (Arch Linux Archive/Arch Linux Historical Archive), como um equivalente ao flakes.lock.

## Contribuindo

Contribuições são a força vital do software de código aberto. Se você tem ideias para melhorar o Ch-aronte, sua ajuda é muito bem-vinda! Confira o `CONTRIBUTING.md` para começar.

Áreas de interesse particular incluem:

- Traduções criativas e melhorias no estilo narrativo.
- Automação do gerenciamento de dotfiles.
- Sugestões e implementações para configurações pós-instalação.
- Criação de issues.

## Agradecimentos

A inspiração principal para este projeto veio do [archible](https://github.com/0xzer0x/archible) do [0xzer0x](https://github.com/0xzer0x).
> Se você está lendo isso (duvido, mas vai que), muito obrigado por sua ferramenta incrível, espero alcançar o nível de criatividade e expertise que você teve para torná-la realidade.

<div align="center">
⁂ Navegue com conhecimento. Instale com estilo. Domine o Arch com alma. ⁂
</div>
