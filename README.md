# 🧝‍♂️ Ch-aronte

**Seu guia pelo submundo do Arch Linux.**

[![Status do Projeto: Ativo](https://img.shields.io/badge/status-ativo-success.svg)](https://github.com/Dexmachi/Ch-aronte)

---

**Ch-aronte** não é apenas um instalador. É uma jornada guiada e interativa pelo coração do Arch Linux, projetada para quem deseja instalar com confiança e aprender o processo de verdade — sem copiar e colar comandos no escuro.

Construído com a robustez do **Ansible** e a interatividade do **Shell Script**, ele automatiza as partes tediosas e te entrega o controle onde importa, transformando uma instalação complexa em uma experiência imersiva.

## ✨ Funcionalidades Principais

* ✅ **Instalação Interativa e Guiada**: Um passo a passo que explica o que está acontecendo.
* ✅ **Detecção Automática de Firmware**: Instalação otimizada para **UEFI (com rEFInd)** ou **BIOS (com GRUB)** sem dor de cabeça.
* ✅ **Sistema de Plugins**: Adicione seus próprios pacotes e, futuramente, gerencie seus dotfiles com presets customizados.
* ✅ **Código Aberto e Didático**: A base de código foi refatorada para ser um exemplo prático e legível de automação.

## 🏛️ A Arquitetura: Orquestrador + Worker

O projeto utiliza uma arquitetura híbrida poderosa e flexível:

* **Shell Script (O Orquestrador)**: Atua como a interface interativa com o usuário, coletando informações, validando entradas e orquestrando a sequência de instalação.
* **Ansible (O Worker)**: Atua no backend, executando as tarefas pesadas de forma declarativa e robusta — particionamento, instalação de pacotes e configuração do sistema.

## 🚀 Começando

Projetado para ser executado diretamente do ambiente Live ISO do Arch Linux.

### Pré-requisitos:

* Conexão com a internet (use `iwctl` no live environment).
* Arch Linux Live ISO em execução.

### Passos da Instalação:

```bash
# 1. No ambiente live, conecte-se à internet
iwctl

# 2. (Opcional, mas recomendado) Aumente o espaço em RAM para o liveboot
mount -o remount,size=2G /run/archiso/cowspace

# 3. Instale as dependências
pacman -Sy --noconfirm ansible git
# 4. Clone o repositório e inicie a instalação
git clone [https://github.com/Dexmachi/Ch-aronte.git](https://github.com/Dexmachi/Ch-aronte.git)
cd Ch-aronte

# IMPORTANTE: Execute o script de dentro da pasta do projeto
chmod +x A-coin.sh
./A-coin.sh
```

> [!WARNING]
> O script é seu guia. Siga as instruções no terminal e deixe que o Ch-aronte te conduza pela instalação.

## 🧩 Sistema de Plugins
Personalize sua instalação criando seus próprios "presets" de pacotes.
1. Crie um arquivo custom-SEU-PLUGIN.yml dentro de ./roles/sistema/vars/.
2. Use o formato abaixo para listar os pacotes desejados:
```YAML
pacotes:
  - neovim
  - fish
  - starship

dotfiles:
  - repo: https://github.com/your-user/your-dotfiles.git
    # Para o script decidir como vai aplicar as dotfiles, você pode inserir de 3 formas:
    install_command: "your_custom_dotfile_command.sh" # FORMA 1: você setta um comando específico de como você instala suas dotfiles. Tenha em mente que o script assume que esse comando será rodado dentro da root do seu repo.
    manager: "stow" # FORMA 2: você setta um manager de dotfiles e o script utiliza ele (por exemplo, o stow aplicar todas suas dots).
    # FORMA 3: não colocar nada faz o script buscar por um script "install.sh" dentro da root do seu repositório de dotfiles.
```
> [!WARNING]
> USE BARRAS DE ESPAÇO AO INVÉS DE TABS, O ANSIBLE É SUPER SENSÍVEL A ISSO.

### Para gerar seu plugin do sistema atual, rode:
```bash
cd Ch-aronte
DIR="./roles/sistema/vars/" && FILENAME="custom-meu-sistema-atual.yml" && mkdir -p "$DIR" && echo "pacotes:" > "$DIR/$FILENAME" && pacman -Qqen | sed 's/^/  - /' >> "$DIR/$FILENAME" && echo "Plugin gerado com sucesso em '$DIR/$FILENAME'!"
```
> [!INFO]
> Funciona diretamente do terminal!

## 🗺️ Roadmap do Projeto
- [x] Instalador Minimal com Detecção de Firmware
- [x] Sistema de Plugins para Pacotes Customizados
- [x] Gerenciador de Dotfiles Integrado ao Sistema de Plugins
- [ ] Modo de Execução Totalmente Automatizado com Arquivo de Configuração

## 🤝 Contribuindo

Contribuições são a alma do software livre. Se você tem ideias para melhorar o Ch-aronte, sua ajuda é muito bem-vinda! Dê uma olhada em CONTRIBUTING.md para começar.

As áreas de maior interesse são:
- Traduções criativas e melhorias na narrativa.
- Automatização do gerenciamento de dotfiles.
- Sugestões e implementações de configurações pós-instalação.
- Criação de issues

## 🙏 Agradecimentos

> A inspiração principal para este projeto veio do [archible](https://github.com/0xzer0x/archible) feito pelo [0xzer0x](https://github.com/0xzer0x). Obrigado por criar uma ferramenta tão incrível e por inspirar a comunidade.

<div align="center">
⁂ Navegue com consciência. Instale com estilo. Domine o Arch com alma. ⁂
</div>

---

### 📋 `README.md` File (English Version - EN-US)

# 🧝‍♂️ Ch-aronte

**Your guide through the Arch Linux underworld.**

[![Project Status: Active](https://img.shields.io/badge/status-active-success.svg)](https://github.com/Dexmachi/Ch-aronte)

---

**Ch-aronte** is not just an installer. It's a guided, interactive journey into the heart of Arch Linux, designed for those who want to install with confidence and truly learn the process—no more blind copy-pasting.

Built with the robustness of **Ansible** and the interactivity of **Shell Script**, it automates the tedious parts and gives you control where it matters, turning a complex installation into an immersive experience.

## ✨ Key Features

* ✅ **Interactive & Guided Installation**: A step-by-step process that explains what's happening.
* ✅ **Automatic Firmware Detection**: Optimized installation for **UEFI (with rEFInd)** or **BIOS (with GRUB)**, hassle-free.
* ✅ **Plugin System**: Add your own packages and, in the future, manage your dotfiles with custom presets.
* ✅ **Open & Readable Code**: The codebase has been refactored to serve as a practical and clean example of automation.

## 🏛️ The Architecture: Orchestrator + Worker

The project uses a powerful and flexible hybrid architecture:

* **Shell Script (The Orchestrator)**: Acts as the interactive frontend, gathering user input, validating data, and orchestrating the installation sequence.
* **Ansible (The Worker)**: Acts as the backend, executing the heavy-lifting tasks declaratively and reliably—partitioning, package installation, and system configuration.

## 🚀 Getting Started

Designed to be run directly from the Arch Linux Live ISO environment.

### Prerequisites:

* An internet connection (use `iwctl` in the live environment).
* A running Arch Linux Live ISO.

### Installation Steps:

```bash
# 1. In the live environment, connect to the internet
iwctl

# 2. (Optional, but recommended) Increase the RAM space for the liveboot
mount -o remount,size=2G /run/archiso/cowspace

# 3. Install the dependencies
pacman -Sy --noconfirm ansible git dialog

# 4. Clone the repository and start the installer
git clone [https://github.com/Dexmachi/Ch-aronte.git](https://github.com/Dexmachi/Ch-aronte.git)
cd Ch-aronte

# IMPORTANT: Run the script from inside the project folder
chmod +x A-coin.sh
./A-coin.sh
```
> [!WARNING]
> The script is your guide. Follow the instructions in the terminal and let Ch-aronte lead you through the installation

## 🧩 Plugin System

Customize your installation by creating your own package presets.
1. Create a file named custom-YOUR-PLUGIN.yml inside ./roles/sistema/vars/.
2. Use the format below to list your desired packages:
```YAML
pacotes:
  - neovim
  - fish
  - starship

dotfiles:
  - repo: https://github.com/your-user/your-dotfiles.git
    # To decide how the script will behave, you have 3 options as to how it will work.
    install_command: "your_custom_dotfile_command.sh" # OPTION 1: install_command is an variable that you can set to decide how the script will install your dotfiles. It uses the root of your repo as a base point, so be aware of that.
    manager: "stow" # OPTION 2: You set an manager and the script applies it to every folder in your repo.
    # OPTION 3: leaving this blank (neither install_command nor manager) makes it so the script searches for a "install.sh" inside of the root of your repo, using it as a basis to install your dotfiles.
```
> [!WARNING]
> USE SPACES INSTEAD OF TABS, ANSIBLE IS VERY SENSITIVE.

### To generate your current system's plugin, run:
```bash
cd Ch-aronte
DIR="./roles/sistema/vars/" && FILENAME="custom-meu-sistema-atual.yml" && mkdir -p "$DIR" && echo "pacotes:" > "$DIR/$FILENAME" && pacman -Qqen | sed 's/^/  - /' >> "$DIR/$FILENAME" && echo "Plugin gerado com sucesso em '$DIR/$FILENAME'!"
```
> [!INFO]
> Works directly from your terminal!


## 🗺️ Project Roadmap

- [x] Minimal Installer with Firmware Detection
- [x] Plugin System for Custom Packages
- [x] Dotfile Manager integrated with the Plugin System
- [ ] Fully Automated Execution Mode with a Config File

## 🤝 Contributing

Contributions are the lifeblood of open-source software. If you have ideas to improve Ch-aronte, your help is very welcome! Check out CONTRIBUTING.md to get started.

Areas of particular interest include:

- Creative translations and improvements to the narrative style.
- Automation of dotfile management.
- Suggestions and implementations for post-install configurations.
- Creation of issues.

## 🙏 Acknowledgements

The primary inspiration for this project came from [archible](https://github.com/0xzer0x/archible) from [0xzer0x](https://github.com/0xzer0x).
> If you're reading this (I doubt it but oh well), thank you very much for your amazing tool, I hope to achieve this level of creativity and expertise you've got to make it come true.

<div align="center">
⁂ Navigate with knowledge. Install with style. Master Arch with soul. ⁂
</div>
