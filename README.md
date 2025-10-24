> [!WARNING]
>
> Some of the features located here are in an beta branch.

[versão pt br](./READMEpt_BR.md)
# Ch-aronte

**An declarative Arch linux installer and manager**

[![Project Status: Active](https://img.shields.io/badge/status-active-success.svg)](https://github.com/Dexmachi/Ch-aronte)

---

***An guided arch-installer and declarative system manager***
***PART OF THE Ch-aOS (Ch-aronte + Ch-imera for nix + Ch-obolos) PROJECT SUITE***

## Key Features

- **An *guided* instalation process**: Instead of automating everything, the script displays a series of questions and explanations about what it's doing to the reader, they gather information about the _how_ the reader wants their system, it then writes an singular file in yaml –for easy readability– and uses _that_ file to install the system, it is not automated at all (Im working on an automated mode)
- **The plugin –or better yet, Ch-obolos– system**: Akin to nix, the Ch-aOS plugin system is fully declarative, written exclusively in yaml, it helps the user manage their whole entire system with one singular file by using ansible + the (WIP) Ch-imera project will be able to take these plugins and compile them into nixlang, allowing for an easy transition.

## The Architecture: Orchestrator + Worker

The project uses a hybrid architecture, delegating to different languages their do's and don't's:

* **Shell Script (The Orchestrator)**: Used to gather user input, transform the input into an declarative file and call in–
* **Ansible (The Worker)**: Used to make sure the system state is the same as the one declared in the Ch-obolo file.

## Getting Started

Run directly from the Arch Linux Live ISO environment.

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
pacman -Sy --noconfirm ansible git yq

# 4. Clone the repository and start the installer
git clone [https://github.com/Dexmachi/Ch-aronte.git](https://github.com/Dexmachi/Ch-aronte.git)
cd Ch-aronte

# IMPORTANT: Run the script from inside the project folder
chmod +x A-coin.sh
./A-coin.sh
```
> [!WARNING]
>
> The script is your guide. Follow the instructions in the terminal and answer the questions, the system will install the system based on it

## Plugin System

Customize your installation by creating your own presets.
1. Create a file named custom-YOUR-PLUGIN.yml inside ./Ch-obolos/.
2. While you can put everything in one file, I recommend separating concerns into multiple files and using a main file to import them. This makes your configuration cleaner and more reusable.

For example, you could have the following structure in your `./Ch-obolos/` directory:
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

Your main file, `custom-main.yml`, would then use `imports` to combine the other files. The `strategy` key (`override`, `combine`, `merge`) determines how data is merged if keys conflict.
```YAML
# ./Ch-obolos/custom-main.yml
# This is the main entrypoint file for your plugin.
plug_name: custom-main.yml # <- essential, this identifies the plugin

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

  # Partitions and region are usually defined by the interactive script,
  # but can also be imported if you are running in a fully declarative mode.
  - file: 'partitions.yml'
    strategy: override

  - file: 'region.yml'
    strategy: override
```

And the corresponding files would contain the specific configurations, for example:
```YAML
# ./Ch-obolos/packages.yml
pacotes:
  - neovim
  - fish
  - starship

bootloader: "grub"
```

Or:
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
  sec_mode: "charonte" #<- later I will add a "system" mode, which requires prior setup of ansible-vault or nix's sops
  sec_file: "Ch-obolos/secrets.yml" #<- secrets file (passwords), must be secret and is REQUIRED for sec_mode "charonte"
```

### Example of a complete file with everything in one:
```YAML
# It's recommended to separate these configurations into different files
# (e.g., users.yml, packages.yml) and use a main plugin file to import them,
# but for this example, everything is in one place.

# Defines system users, groups, and hostname
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
wheel_access: true # Grants sudo access to the 'wheel' group

# Defines the list of packages to be declaratively managed
pacotes:
  - neovim
  - fish
  - starship
  - btop
bootloader: "grub" # or "refind"

# pacotes_base_override: <~ very dangerous, it allows you to change the core base packages (e.g: linux linux-firmware ansible ~cowsay~ etc)

# Manages systemd services
services:
  - name: "NetworkManager"
    state: "started"
    enabled: true
  - name: "bluetooth"
    state: "started"
    enabled: true

# Manages pacman repositories
repos:
  managed:
    extras: true      # Enables the [extras+multilib] repository
    unstable: false   # Disables the [testing] repositories
  third_party:
    - name: "cachyOS"
      distribution: "arch"
      url: "https://mirror.cachyos.org/cachyos-repo.tar.xz"

# Manages dotfiles from git repositories
dotfiles:
  - repo: https://github.com/your-user/your-dotfiles.git
    # To decide how the script will behave, you have 3 options as to how it will work.
    install_command: "your_custom_dotfile_command.sh"
    # OPTION 1: install_command is a variable that you can set to decide how the script will install your dotfiles.
    # It uses the root of your repo as a base point, so be aware of that.
    manager: "stow"
    # OPTION 2: You set a manager and the script applies it to every folder in your repo.
    # OPTION 3: leaving this blank (neither install_command nor manager) makes it so the script searches for an "install.sh" file inside the root of your repo, using it as a basis to install your dotfiles.

# Defines disk partitions (usually filled by the interactive script)
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

# Defines region, language, and keyboard settings
region:
  timezone: "America/Sao_Paulo"
  locale:
    - "pt_BR.UTF-8"
    - "en_US.UTF-8"
  keymap: "br-abnt2"

```

### To generate your current system's plugin, run:
```bash
cd Ch-aronte
DIR="./Ch-obolos/" && FILENAME="custom-meu-sistema-atual.yml" && mkdir -p "$DIR" && echo "pacotes:" > "$DIR/$FILENAME" && pacman -Qqen | sed 's/^/  - /' >> "$DIR/$FILENAME" && echo "Plugin gerado com sucesso em '$DIR/$FILENAME'!"
```

## Project Roadmap

- [-] = In Progress, probably in another branch, either being worked on or already implemented, but not fully tested.

### MVP
- [x] Minimal Installer with Firmware Detection
- [x] Plugin System for Custom Packages

### Modularity + Automation
- [x] Dotfile Manager integrated with the Plugin System
- [x] Import system (hell)
- [ ] B-coin system manager CLI helper.

### Declarativity
- [-] Fully declarative installation mode, with it's only necessity being the custom*.yml file. (I just need to implement the checker on the start of the script and if the plugin file exists and is selected, run in declarative mode)
- [-] Fully declarative post-install system configuration with only one custom*.yml file. (I just need to implement the B-coin helper for this one)
- [x] Declarative package state manager (Install and uninstall declaratively).
- [x] Repo manager.

### Quality + security
- [-] ansible-lint and ansible-test tests. (Currently being done manually)

### Ideas being studied
- [-] Secrets management (HIGHLY expansible, currently only used for user passwords).
- [ ] ALA/ALHA (Arch Linux Archive/Arch Linux Historical Archive) Support, as a flakes.lock equivalent.

## Contributing

Contributions are higly welcomed. If you have ideas to improve Ch-aronte, your help is very welcome! Check out CONTRIBUTING.md to get started.

Areas of particular interest include:

- Creative translations and improvements to the narrative style.
- Suggestions and implementations for post-install configurations.
- Help to check if the Ch-obolos are truly declarative or not.
- Creation of issues.

## Acknowledgements

The primary inspiration for this project came from [archible](https://github.com/0xzer0x/archible) from [0xzer0x](https://github.com/0xzer0x).
> If you're reading this (I doubt it but oh well), thank you very much for your amazing tool, I hope to achieve this level of creativity and expertise you've got to make it come true.
