[versão pt br](./READMEpt_BR.md)
# Ch-aronte

**Your guide through the Arch Linux underworld.**

[![Project Status: Active](https://img.shields.io/badge/status-active-success.svg)](https://github.com/Dexmachi/Ch-aronte)

---

**Ch-aronte** is not just an installer. It's a guided, interactive journey into the heart of Arch Linux, designed for those who want to install with confidence and truly learn the process—no more blind copy-pasting.

Built with the robustness of **Ansible** and the interactivity of **Shell Script**, it automates the tedious parts and gives you control where it matters, turning a complex installation into an immersive experience.

## Key Features

* **Interactive & Guided Installation**: A step-by-step process that explains what's happening.
* **Automatic Firmware Detection**: Optimized installation for **UEFI (with rEFInd)** or **BIOS (with GRUB)**, hassle-free.
* **Plugin System**: Add your own packages and, in the future, manage your dotfiles with custom presets.
* **Open & Readable Code**: The codebase has been refactored to serve as a practical and clean example of automation.

## The Architecture: Orchestrator + Worker

The project uses a powerful and flexible hybrid architecture:

* **Shell Script (The Orchestrator)**: Acts as the interactive frontend, gathering user input, validating data, and orchestrating the installation sequence.
* **Ansible (The Worker)**: Acts as the backend, executing the heavy-lifting tasks declaratively and reliably—partitioning, package installation, and system configuration.

## Getting Started

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

## Plugin System

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


## Project Roadmap

- [x] Minimal Installer with Firmware Detection
- [x] Plugin System for Custom Packages
- [-] Dotfile Manager integrated with the Plugin System
- [ ] Fully Automated Execution Mode with a Config File
- [ ] ALA/ALHA (Arch Linux Archive/Arch Linux Historical Archive) Support, as a flakes.lock equivalent.
- [ ] Fully declarative installation mode, with it's only necessity being the custom*.yml file.
- [ ] Fully declarative post-install system configuration with only one custom*.yml file.
- [ ] Package manager akin to nixpkgs, with a declarative package list and versioning.
- [ ansible-lint and ansible-test tests.

MAYBE ILL IMPLEMENT THIS, BUT IDK:
- [ ] Secrets management (I'm already implementing this with ansible vault, hashing or even just plain text for user passwords {user's choice}, but maybe I can make smth for wifi passwords, git tokens, ssh keys and son on and so forth).

## Contributing

Contributions are the lifeblood of open-source software. If you have ideas to improve Ch-aronte, your help is very welcome! Check out CONTRIBUTING.md to get started.

Areas of particular interest include:

- Creative translations and improvements to the narrative style.
- Automation of dotfile management.
- Suggestions and implementations for post-install configurations.
- Creation of issues.

## Acknowledgements

The primary inspiration for this project came from [archible](https://github.com/0xzer0x/archible) from [0xzer0x](https://github.com/0xzer0x).
> If you're reading this (I doubt it but oh well), thank you very much for your amazing tool, I hope to achieve this level of creativity and expertise you've got to make it come true.

<div align="center">
⁂ Navigate with knowledge. Install with style. Master Arch with soul. ⁂
</div>
