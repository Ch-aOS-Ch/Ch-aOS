
[versão pt br](./READMEpt_BR.md)
# ***Ch-aOS project suite***

[![Project Status: Active](https://img.shields.io/badge/status-active-success.svg)](https://github.com/Dexmachi/Ch-aronte)
## What is it about?

- Ch-aOS is meant to be a way to declaratively manage your linux system, from installation to post-install configuration, in a modular, safe, and didactic way.

## How does it work?

- The chaos CLI uses Python, Pyinfra and OmegaConf as it's main engine, allowing for a declarative paradigm approach in a simpler way.
- It also uses sops as its main encryption engine, orchestrating multiple of sops' commands and configurations in order to provide a safe environment.
- It allows for modularity through plugins, meaning that you can extend it's functionality by adding new plugins to it, either made by me or by the community.
- My plugins include: Ch-aronte (an Arch Linux core), chaos-dots (a dotfile manager), and chaos-secrets, a secrets templater that uses jinja2 for sops.

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
> You can use `chaos set sops/chobolo/secrets` to set your base chobolo file, secrets file or sops file, this will be used as the base for all role runs and decryptions!

> [!TIP]
>
> You can complete example of a Ch-obolo in [My-Ch-obolos](Ch-obolos/dex/dex-migrating.yml), these are the Ch-obolos I am actively using to manage my own system!

> [!TIP]
>
> Want to test a chaos role but don't want to mess with your system? Use chaos -dvvv to run it in dry-run + full verbose mode, this way you can see exactly what it is doing without actually doing it! Also, all roles (made by me) ask for confirmation before doing _anything_ potentially destructive, so you are always safe by design. (unless you use -y, then you're on your own)

## Secret Providers
*   **What are they?** Secret `providers` in Ch-aOS are integrations with external password managers (like Bitwarden and 1Password). They allow the `chaos` CLI to access encryption keys (AGE, GPG, Vault tokens) securely stored in these services, without needing to keep them permanently on the local filesystem.
*   **Why use them?** The main advantage is enhanced security and convenience. Instead of managing key files locally, `chaos` can fetch the necessary keys *ephemerally* (just for the duration of an operation) from your configured secret provider!
*   **How are they used?**
    *   **Configuration:** You can configure default secret providers inside the `secret_providers` part of ~/.config/chaos/config.yml file, the only hardcoded key inside of this is "default", the rest you can set as you wish, just be sure to create them using sub dicts (eg. provider.key_id).
    *   **Usage in Commands:** Many commands that interact with secrets (like `chaos apply`, `chaos secrets edit`, `chaos secrets print`, `chaos ramble edit`, `chaos ramble read`) accept specific flags to use a provider:
        *   `-p [provider_name]`: Uses a provider configured in your `~/.config/chaos/config.yml` file. You can optionally specify a named provider (e.g., `bw.age` for Bitwarden with an AGE key). If no name is given, it will try to use the `default` provider.
        *   `-b <ITEM_ID> <KEY_TYPE>`: Uses a key directly from a Bitwarden item.
        *   `-bs <ITEM_ID> <KEY_TYPE>`: Uses a key directly from a Bitwarden Secrets item.
        *   `-o <URL> <KEY_TYPE>`: Uses a key directly from a 1Password item (via URL).
    *   **Export/Import:** The `chaos secrets export` command allows you to export SOPS keys to a secret provider, and `chaos secrets import` allows you to import them locally.

## Team Management
*   **What is it?** The team management feature in Ch-aOS is designed to facilitate collaboration and the sharing of configurations and secrets within a work group. It establishes a standardized structure for team repositories, allowing members to share `ramblings` (encrypted notes), secret files, and declarative configurations in an organized and secure way.
*   **Why use it?**
    *   **Secure Collaboration:** Allows different team members to access and manage secrets and configurations relevant to their projects, using integrated access control mechanisms (like Shamir's Secret Sharing in SOPS).
    *   **Standardized Structure:** Enforces a directory hierarchy for secrets and `ramblings` (e.g., `secrets/dev`, `secrets/prod`, `ramblings/company/team/person`), making organization and understanding easier.
    *   **Clear Workflows:** Offers dedicated commands to initialize, clone, activate, and deactivate team environments, simplifying new member onboarding and project maintenance.
*   **How is it used?**
    *   **Naming Convention:** Teams are identified by a `company.team.person` convention (e.g., `MyCompany.DevTeam.MyName`). This hierarchy is used to organize files and control access.
    *   **Initialization:** The command `chaos team init MyCompany.DevTeam.MyName` creates a new team repository locally, setting up the directory structure for secrets and `ramblings`, and generating a `sops-config.yml` file made for team secret sharing (this uses a LOT of Shamir Secret Sharing, so be sure to educate yourself on that!).
    *   **Cloning and Activation:** Team members can clone an existing team repository (`chaos team clone <REPO_URL>`) and activate it (`chaos team activate [path]`). Activation creates symlinks, registering the team in your local Ch-aOS environment (~/.local/share/chaos).
    *   **Deactivation and Pruning:** Commands like `chaos team deactivate` and `chaos team prune` help remove or clean up records of no-longer-used teams.

# Command Cheat Sheet (cause no good CLI project is complete without one):

The `chaos` CLI is the main entry point for interacting with the Ch-aOS suite. It provides a set of commands to manage your system declaratively, handle secrets, organize your notes, and extend its functionality through plugins. Below is a comprehensive list of all available commands and their options.

#### Global Flags
| Flag | Description |
|------|-------------|
| `-c /path/to/chobolo.yml` | Override the Ch-obolo file for a single run. |
| `-u`, `--update-plugins` | Force an update of the plugin cache. |
| `-t`, `--generate-tab` | Generate a shell tab-completion script. |
| `-ec`, `--edit-chobolo` | Edit your chobolo file with `$EDITOR`. |
| `-h`, `--help` | Show the help screen. |

#### `apply`
Applies one or more roles to the system.
| Flag | Description |
|------|-------------|
| `tags...` | A space-separated list of roles/aliases to execute. |
| `-c /path/to/chobolo.yml` | Override the Ch-obolo file for this run. |
| `-d`, `--dry` | Dry-run mode (preview changes without executing). |
| `-v`, `-vv`, `-vvv` | Increase verbosity level. |
| `--verbose [1-3]` | Set verbosity level directly. |
| `-s`, `--secrets` | Signal that a role requires secret decryption. |
| `-sf /path/to/secrets.yml`| Override the secrets file for this run. |
| `-ss /path/to/sops.yml` | Override the sops config file for this run. |
| `-t team` | Specify the team to use (e.g., `company.team.group`). |
| `-p [provider]` | Use a configured provider for decryption (e.g., `bw.age`). Uses `default` if no name is given. |
| `-b <ID> <type>` | [Manual] Decrypt with a key from Bitwarden. |
| `-bs <ID> <type>` | [Manual] Decrypt with a key from Bitwarden Secrets. |
| `-o <url> <type>` | [Manual] Decrypt with a key from 1Password. |
| `-ikwid`, `--i-know-what-im-doing` (or just `-y` if you're boring) | "I Know What I'm Doing" mode (disables safety checks). |

#### `check`
Lists available items like roles, aliases, and explanations.
| Argument | Description |
|----------|-------------|
| `roles` | List all available roles. |
| `aliases` | List all available aliases. |
| `explanations`| List all available explanation topics. |

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
*Run `chaos ramble <subcommand> -h` for detailed options.*
| Subcommand | Description |
|------------|-------------|
| `create <target>` | Create a new ramble or a rambling inside a ramble (e.g., `journal.page`). |
| `edit <target>` | Edit a rambling directly, whether encrypted or not (e.g., `journal.page`). |
| `encrypt <target>` | Encrypt a rambling inside a ramble with sops (e.g., `journal.page`). |
| `read <targets...>` | Read your ramblings. Use `journal.list` to list ramblings or `journal.page` to read a specific one. |
| `find [term]` | Find rambles by keyword or tag. |
| `move <old> <new>` | Move a rambling (e.g., `journal.old_page`) to a new location (e.g., `new_journal.new_page`). |
| `update` | Update your rambling encryption keys. |
| `delete <ramble>` | Delete a rambling (e.g., `journal.page`) or an entire ramble (e.g., `journal`). |

#### `secrets`
A powerful suite for managing application secrets using `sops`.
*Run `chaos secrets <subcommand> -h` for detailed options.*
| Subcommand | Description |
|------------|-------------|
| `cat <keys...>` | Decrypts and prints specific keys from the secrets file. |
| `edit` | Edit the encrypted secrets file in-place. |
| `export <backend>` | Export sops keys to a password manager (`bw`, `bws`, `op`). |
| `import <backend>` | Import sops keys from a password manager (`bw`, `bws`, `op`). |
| `list <type>` | List all keys of a given type (`age`, `pgp`, `vault`) in the sops config. |
| `print` | Decrypt and print the entire secrets file to stdout. |
| `rotate-add <type> <keys...>` | Add new keys (`age`, `pgp`, `vault`) to the sops configuration. |
| `rotate-rm <type> <keys...>` | Remove keys (`age`, `pgp`, `vault`) from the sops configuration. |
| `shamir <index> <shares>` | Configure Shamir's Secret Sharing for a specific rule. |

#### `team`
Manages team configurations and repositories for collaborative development.
*Run `chaos team <subcommand> -h` for detailed options.*
| Subcommand | Description |
|------------|-------------|
| `activate [path]` | Activate a team from a local repository. |
| `clone <repo_url>` | Clone a team repository from a git URL. |
| `deactivate <company> [teams...]` | Deactivate one or more teams for a company. |
| `init <company.team.person>` | Initialize a new team repository in the current directory. |
| `list [company]` | List all activated teams, optionally filtering by company. |
| `prune [companies...]` | Remove stale team symlinks that point to non-existent directories. |

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

