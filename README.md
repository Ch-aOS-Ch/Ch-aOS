[versão pt br](./READMEpt_BR.md)
# ***Ch-aOS project suite***

[![Project Status: Active](https://img.shields.io/badge/status-active-success.svg)](https://github.com/Dexmachi/Ch-aronte)

***Ch-aronte for Arch; Ch-imera for NixOS; Ch-obolos for it all. Studying the viablity of a Ch-iron for Fedora and Ch-ronos for Debian.***

## What is it about?

- Ch-aOS is meant to be a way to declaratively manage your linux system, from installation to post-install configuration, in a modular way.

## How does it work?

- the chaos CLI uses Python, Pyinfra and OmegaConf as it's main engine, allowing for a declarative paradigm approach in a simpler way.
- Ch-aronte is only a plugin module that gives chaos it's "roles", a pluggable backend made for Arch Linux systems.
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
2. Go to ./cli/build/b-coin/ and run `makepkg -fcsi` to install the chaos CLI.
3. (optional) go to ../../Ch-aronte/build/core and run `makepkg -fcsi` to install the Ch-aronte core.
4. (optional) go to ../../external_plugins/chaos-dots and run `makepkg -fcsi` to install the chaos-dots plugin.
5. Now you can run `chaos -h` to see the help menu and `chaos check [roles/explanations/aliases/secrets]`!

## Ch-obolos System
It's a declarative yaml file describing what your system should have! Ch-aOS will load this file and utilize it's keys for managing your system for you.

> [!TIP]
>
> You can use `chaos -chobolo/sec/sops` to set your base chobolo file, secrets file or sops file, this will be used as the base for all role runs and decryptions!

> [!WARNING]
>
> You can complete example of a Ch-obolo in [My-Ch-obolos](Ch-obolos/dex/dex-migrating.yml), these are the Ch-obolos I am actively using to manage my own system!

> [!TIP]
>
> Want to test the chaos role but don't want to mess with your system? Use chaos -dvvv to run it in dry-run + full verbose mode, this way you can see exactly what it is doing without actually doing it! Also, all roles (made by me) ask for confirmation before doing _anything_ potentially destructive, so you are always safe by design. (unless you use -y, then you're on your own)

# Command Cheat Sheet (cause no good CLI project is complete without one):
#### Global Flags
| Flag | Description |
|------|-------------|
| `-c /path/to/chobolo.yml` | Override the Ch-obolo file for a single run. |
| `-sf /path/to/secrets.yml`| Override the secrets file for a single run. |
| `-ss /path/to/sops.yml` | Override the sops config file for a single run. |
| `-u`, `--update-plugins` | Force an update of the plugin cache. |
| `-t`, `--generate-tab` | Generate a shell tab-completion script. |
| `-es`, `--edit-sec` | Edit your secrets file using `sops`. |
| `-ec`, `--edit-chobolo` | Edit your chobolo file with `$EDITOR`. |
| `-h`, `--help` | Show the help screen. |

#### `apply`
Applies one or more roles to the system.
| Flag | Description |
|------|-------------|
| `tags...` | A space-separated list of roles/aliases to execute. |
| `-d`, `--dry` | Dry-run mode (preview changes without executing). |
| `-v`, `-vv`, `-vvv` | Increase verbosity level. |
| `--verbose [1-3]` | Set verbosity level directly. |
| `-ikwid`, `--i-know-what-im-doing` (or just `-y` if you're boring) | "I Know What I'm Doing" mode (disables safety checks). |

#### `check`
Lists available items like roles, aliases, and explanations.
| Argument | Description |
|----------|-------------|
| `roles` | List all available roles. |
| `aliases` | List all available aliases. |
| `explanations`| List all available explanation topics. |
| `secrets` | Decrypt and print the secrets file to stdout. |

#### `explain`
Provides detailed explanations for roles and topics.
| Argument | Description |
|----------|-------------|
| `topic` or `topic.subtopic` | The topic to explain. Use `topic.list` to see subtopics. |
| `-d [basic\|intermediate\|advanced]` | Set the level of detail for the explanation. |

#### `init`
Creates boilerplate configuration files.
| Argument | Description |
|----------|-------------|
| `chobolo` | Generate a template `ch-obolo.yml` from installed plugins. |
| `secrets` | Interactively set up `sops` and create an initial `secrets.yml`. |

#### `set`
Sets the default paths for configuration files.
| Argument | Description |
|----------|-------------|
| `chobolo /path/to/file.yml` | Set the default Ch-obolo file. |
| `secrets /path/to/file.yml` | Set the default secrets file. |
| `sops /path/to/file.yml` | Set the default sops config file. |

#### `ramble`
A built-in, encrypted note-taking utility.
* `chaos ramble create journal.page`
* `chaos ramble edit journal.page`
* `chaos ramble read journal.page`
* `chaos ramble find "keyword"`
* ... and more! Run `chaos ramble -h` for all commands.

# Example of usage:
![chaos usage](./imagens/B-coin-test.gif)

## Project Roadmap

- [-] = In Progress, probably in another branch, either being worked on or already implemented, but not fully tested.

### Next on the chopping board:
- [ ] Ch-imera
- [ ] Installer

### MVP
- [-] Minimal Installer with Firmware Detection
- [x] Plugin System for Ch-aronte
- [x] Declarative package state manager (Install and uninstall declaratively) for Ch-aOS.

### Modularity + Automation
- [x] Dotfile Manager integrated with the Plugin System
- [x] chaos system manager CLI helper.
- [ ] Ch-imera Ch-obolo transpiler for simple nix 

### Declarativity
- [-] Fully declarative installation mode, with it's only necessity being the *.yml file for Ch-aOS.
- [x] Fully declarative post-install system configuration with only one custom*.yml file for Ch-aOS.
- [x] Repo manager for Ch-aronte.
- [x] Secrets management.
  - Utilizes sops as a secrets manager.
  - Utilizes Jinja2 for templating.

### Quality + security
- [-] Pytest + flake8 tests for all the codebase.

### Ideas being studied
- Ch-iron -- a fedora core for Ch-aOS
- Ch-ronos -- a debian core for Ch-aOS
- mapping for distro agnosticity (probably impossible)

## Contributing

Contributions are higly welcomed. If you have ideas to improve Ch-aOS, your help is very welcome! Check out CONTRIBUTING.md to get started.

Areas of particular interest include:

- Creative translations and improvements to the narrative style.
- Suggestions and implementations for post-install configurations.
- Help to check if the Ch-obolos are truly declarative or not.
- Creation of issues.

## Acknowledgements

The primary inspiration for this project came from [archible](https://github.com/0xzer0x/archible) from [0xzer0x](https://github.com/0xzer0x).
> If you're reading this (I doubt it but oh well), thank you very much for your amazing tool, I hope to achieve this level of creativity and expertise you've got to make it come true.
