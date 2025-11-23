[versão pt br](./READMEpt_BR.md)
***Ch-aOS project suite***

[![Project Status: Active](https://img.shields.io/badge/status-active-success.svg)](https://github.com/Dexmachi/Ch-aronte)

***Ch-aronte for Arch; Ch-imera for NixOS; Ch-obolos for it all. Studying the viablity of a Ch-iron for Fedora and Ch-ronos for Debian.***

## What is it about?

- Ch-aOS is meant to be a way to declaratively manage your linux system, from installation to post-install configuration, in a modular way.

## How does it work?

- the chaos CLI uses Python, Pyinfra and OmegaConf as it's main engine, allowing for an declarative paradigm approach in a more simple way.
- Ch-aronte is only a pluggable module that gives chaos it's "roles", a pluggable backend made for Arch Linux systems.
- Ch-imera will be a little bit different, it will _transpile_ the Ch-obolos files into simple nix expressions, allowing for a _kickstart_ into NixOS systems, basically letting you "test drive" the declarative paradigm without needing to learn it inside of a "pure declarative" system.
- Ch-obolo is the main configuration system, it is meant to be a universal configuration for all of the Ch-aOS projects, letting you distro-hop with ease.

## Did you say plugins??
- Yes! The chaos CLI is basically just the CLI itself, with no backends at all, the backends are plugins themselves, this means that you can create your own backend for your own distro if you want to!
- Some examples of possible backends are found inside of the external_plugins folder, including a mock backend for testing and a chaos-dots backend for dotfile management! (This one i use myself!)

### But what about... yk... actually managing my _system_??
- That's where the "cores" come in, cores are just pre-made plugins that manage specific distros, like Ch-aronte for Arch Linux!
- These are made by me, myself and I, but anyone can create their own core if they want to... yk... cause they're plugins.
- Cores should contain all the bare minimum to manage a system, such as package management, user management, service management, etc.

## Getting Started

1. Clone this repo (i'm working on making it pip/aur installable, but for now, this is the only way to get it)
2. To ./cli/build/b-coin/ and run `makepkg -fcsi` to install the chaos CLI.
3.(optional) go to ../../Ch-aronte/build/core and run `makepkg -fcsi` to install the Ch-aronte core.
4. (optional) go to ../../external_plugins/chaos-dots and run `makepkg -fcsi` to install the chaos-dots plugin.
5. Now you can run `chaos -h` to see the help menu and `chaos -r` to check all available roles!
> [!TIP]
>
> sops is highly recommended, it is used for secrets management. Right now it is not a full on dependency, but some features will not work without it and the non use of it will be deprecated in the future.

## Ch-obolos System

> [!TIP]
>
> You can use `chaos -chobolo/sec/sops` to set your base chobolo file, secrets file or sops file, this will be used as the base for all role runs and decryptions!

### Example of a Ch-aronte Ch-obolos file:
```YAML
# Defines system users, groups, and hostname
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
  sec_file: /absolute/path/to/Ch-obolos/secrets-here.yml # <~ Not necessary if you've set it with the chaos CLI, but it can be used as a fallback!
  sec_sops: /absolute/path/to/Ch-obolos/sops-secs.yml # <~ Not necessary if you've set it with the chaos CLI, but it can be used as a fallback!

packages:
  - neovim
  - fish
  - starship
  - btop

aurPackages: # <~ yeah, I sepparated them, this is a safety net for when you DON'T have a damn aur helper (how could you?)
  - 1password-cli
  - aurroamer # <~ Highly recommend, very good package
  - aurutils
  - bibata-cursor-theme-bin
 
bootloader: "grub" # or "refind"

# baseOverride:  <~ very dangerous, it allows you to change the core base packages (e.g: linux linux-firmware ansible ~~cowsay~~ etc)
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

# Manages systemd services
services:
  - name: NetworkManager
    running: True # <~ defaults to True
    on_boot: true # <~ since it defaults to True
                  # I like to keep these for granularity
    dense_service: true # <~ this tells the script to use regex to find all services with "NetworkManager" in it's name

  - name: bluetooth
    dense_service: true # <~ Cause i don't want to put .service every time

  - name: sshd # <~ auto puts .service lmao

  - name: nvidia
    dense_service: true

  - name: sddm.service

# Manages pacman repositories
repos:
  managed:
    core: True      # Enables the [core] repository (default: true)
    extras: true      # Enables the [extras+multilib] repository (default: false)
    unstable: false   # Disables the [testing] repositories (default: false)
  third_party:
    - name: "cachyOS" # <~ you can add as many third party repos as you want, as long as you have them installed
      include: /etc/pacman.d/cachyos-mirrorlist
      distribution: "arch"

# Manages dotfiles from git repositories
dotfiles:
  - url: https://github.com/your-user/your-dotfiles.git
    user: dexmachina # <~ user where the dotfiles will be applied
    branch: main # <~ optional, defaults to main
    pull: true # <~ optional, defaults to false, if true, it will pull the latest changes
    links:
      - from: "zsh" # <~ this is a _folder_ inside of my dotfiles folder
        to: . # <~ this is . by default, it takes the home of the declared user as a base point.
        open: true # <~ defines if the script should symlink the files _inside_ the folder _or_ the folder itself. (defaults to false)
      - from: "bash"
        open: true
      - from: ".config"
# ATTENTION: _ALL_ THE FILES YOU PUT HERE _AND_ ALREADY EXIST ARE BACKED UP BESIDE THE NEW ONES. IF YOU _REMOVE_ A FILE FROM THE LIST, IT WILL BE REMOVED FROM THE PATH YOU SET AS WELL. (duh, it's declarative)

# Defines disk partitions (usually filled by the interactive script)
partitioning: # <~ is not and never will be translatable to a configurations.nix :( but it is translatable to a disko.nix :)
  disk: "/dev/sdb" # <~ what disk you want to partition into
  partitions:
    - name: chronos # <~ Ch-aronte uses label for fstab andother things, this changes nothing to your overall experience, but it is a commodity for me
      important: boot # <~ Only 4 of these, boot, root, swap and home, it uses this to define how the role should be treated (mainly boot and swap)
      size: 1GB # <~ Use G, MiB might work, but it might not, it's still not well stabilized
      mountpoint: "/boot" # <~ required (duh)
      part: 1 # <~ this tells what partition it is (sdb1,2,3,4...)
      type: vfat # <~ or ext4, btrfs, well, you get the idea

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

# Defines region, language, and keyboard settings
region:
  timezone: "America/Sao_Paulo"
  locale:
    - "pt_BR.UTF-8"
    - "en_US.UTF-8"
  keymap: "br-abnt2"

```
> [!WARNING]
>
> You can find a more complete example in [My-Ch-obolos](Ch-obolos/dex/dex-migrating.yml), these are the Ch-obolos I am actively using to manage my own system!

# Example of usage:
![chaos usage](./imagens/B-coin-test.gif)

## Project Roadmap

- [-] = In Progress, probably in another branch, either being worked on or already implemented, but not fully tested.

### MVP
- [-] Minimal Installer with Firmware Detection
- [x] Plugin System for Ch-aronte

### Modularity + Automation
- [x] Dotfile Manager integrated with the Plugin System
- [x] chaos system manager CLI helper.

### Declarativity
- [-] Fully declarative installation mode, with it's only necessity being the *.yml file for Ch-aronte.
- [x] Fully declarative post-install system configuration with only one custom*.yml file for Ch-aronte.
- [x] Declarative package state manager (Install and uninstall declaratively) for Ch-aronte.
- [x] Repo manager for Ch-aronte.

### Quality + security
- [-] Pytest + flake8 tests for all the codebase.

### Ideas being studied
- [-] Secrets management (HIGHLY expansible, currently only used for user passwords).
  - Now that I finally integrated [sops](https://github.com/getsops/sops) to the system, I can easily do secrets management with encryption and safe commiting.

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
