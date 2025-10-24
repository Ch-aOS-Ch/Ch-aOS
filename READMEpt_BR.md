> [!WARNING]
>
> Algumas das funcionalidades aqui localizadas estão em um branch beta.

[english version](./README.md)
# Ch-aronte

**Um instalador e gerenciador declarativo para Arch Linux**

[![Status do Projeto: Ativo](https://img.shields.io/badge/status-ativo-success.svg)](https://github.com/Dexmachi/Ch-aronte)

---

***Um instalador arch guiado e gerenciador de sistema declarativo***
***PARTE DA SUÍTE DE PROJETOS Ch-aOS (Ch-aronte + Ch-imera para nix + Ch-obolos)***

## Funcionalidades Principais

- **Um processo de instalação *guiado***: Em vez de automatizar tudo, o script exibe uma série de perguntas e explicações sobre o que está fazendo para o leitor, eles coletam informações sobre _como_ o leitor quer seu sistema, ele então escreve um arquivo singular em yaml –para fácil legibilidade– e usa _esse_ arquivo para instalar o sistema, não é totalmente automatizado (estou trabalhando em um modo automatizado)
- **O sistema de plugins –ou melhor, Ch-obolos–**: Semelhante ao nix, o sistema de plugins Ch-aOS é totalmente declarativo, escrito exclusivamente em yaml, ele ajuda o usuário a gerenciar todo o seu sistema com um único arquivo usando ansible + o projeto (WIP) Ch-imera será capaz de pegar esses plugins e compilá-los em nixlang, permitindo uma transição fácil.

## A Arquitetura: Orquestrador + Executor

O projeto utiliza uma arquitetura híbrida, delegando a diferentes linguagens seus prós e contras:

* **Shell Script (O Orquestrador)**: Usado para coletar a entrada do usuário, transformar a entrada em um arquivo declarativo e chamar o–
* **Ansible (O Executor)**: Usado para garantir que o estado do sistema seja o mesmo que o declarado no arquivo Ch-obolo.

## Começando

Execute diretamente do ambiente Live ISO do Arch Linux.

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
>
> O script é seu guia. Siga as instruções no terminal e responda às perguntas, o sistema será instalado com base nisso

## Sistema de Plugins

Personalize sua instalação criando seus próprios presets.
1. Crie um arquivo chamado custom-SEU-PLUGIN.yml dentro de ./Ch-obolos/.
2. Embora você possa colocar tudo em um único arquivo, recomendo separar as responsabilidades em múltiplos arquivos e usar um arquivo principal para importá-los. Isso torna sua configuração mais limpa e reutilizável.

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
plug_name: custom-main.yml # <- essencial, isso identifica o plugin

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

### Exemplo de um arquivo completo com tudo em um:
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

# pacotes_base_override: <~ muito perigoso, permite que você altere os pacotes base do núcleo (ex: linux linux-firmware ansible ~cowsay~ etc)

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

### Para gerar o plugin do seu sistema atual, execute:
```bash
cd Ch-aronte
DIR="./Ch-obolos/" && FILENAME="custom-meu-sistema-atual.yml" && mkdir -p "$DIR" && echo "pacotes:" > "$DIR/$FILENAME" && pacman -Qqen | sed 's/^/  - /' >> "$DIR/$FILENAME" && echo "Plugin gerado com sucesso em '$DIR/$FILENAME'!"
```

## Roadmap do Projeto

- [-] = Em Progresso, provavelmente em outra branch, seja sendo trabalhado ou já implementado, mas não totalmente testado.

### MVP
- [x] Instalador Mínimo com Detecção de Firmware
- [x] Sistema de Plugins para Pacotes Customizados

### Modularidade + Automação
- [x] Gerenciador de Dotfiles integrado ao Sistema de Plugins
- [x] Sistema de importação (inferno)
- [ ] Helper de linha de comando para gerenciador de sistema B-coin.

### Declaratividade
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

Contribuições são muito bem-vindas. Se você tem ideias para melhorar o Ch-aronte, sua ajuda é muito bem-vinda! Confira o `CONTRIBUTING.md` para começar.

Áreas de interesse particular incluem:

- Traduções criativas e melhorias no estilo narrativo.
- Sugestões e implementações para configurações pós-instalação.
- Ajuda para verificar se os Ch-obolos são verdadeiramente declarativos ou não.
- Criação de issues.

## Agradecimentos

A inspiração principal para este projeto veio do [archible](https://github.com/0xzer0x/archible) do [0xzer0x](https://github.com/0xzer0x).
> Se você está lendo isso (duvido, mas vai que), muito obrigado por sua ferramenta incrível, espero alcançar o nível de criatividade e expertise que você teve para torná-la realidade.
