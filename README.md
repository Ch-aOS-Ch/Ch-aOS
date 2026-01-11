
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

---

# key features

## Declarative System Orchestration
*   **What is it?** At its core, Ch-aOS allows you to define the desired state of your system in simple YAML files called "Ch-obolos". The `chaos apply` command then reads this data and executes "roles" (Python scripts using `pyinfra`) to make your system's actual state match the declared state.
*   **Why use it?** It enforces a strict separation of data (what your system should be) from logic (how to achieve that state). This makes your configurations readable, reusable, and version-controllable. You can apply specific parts of your configuration (e.g., just users or just packages) without running through everything.
*   **How is it used?**
    *   **Create a Ch-obolo file:** Define variables for your system, like `users`, `packages`, or `services` inside of YAML dicts, these should be documented by the plugin itself (maybe even on `chaos explain`), if a plugin is well made, it will also come with a `keys` entry_point to make sure `chaos init chobolo` can handle the boiler plates for you.
    *   **Apply roles:** Run `chaos apply <role_tag>` (e.g., `chaos apply users pkgs`). Ch-aOS finds the corresponding roles from its installed plugins and executes them, using the data from your Ch-obolo, optionally you can run with the `-s/--secrets` flag to make sure your secrets are loaded as well (don't forget to configure your `.config/chaos/config.yml` so the plugin is recognized as a secret-having plugin as well!).
    *   **Safety First:** Use `chaos apply --dry` (or `-d`) to see a preview of all the changes that would be made without actually applying them, if you really want to get to understand what exactly the plugin is doing, run wit `-vvv` for maximum verbosity.

## Fleet Management
*   **What is it?** The `fleet` feature extends `chaos` to multi-machine orchestration. By adding a `fleet` block to your Ch-obolo file, you can define a group of remote hosts and run `chaos apply --fleet` roles across all of them simultaneously.
*   **Why use it?** It's essential for managing any infrastructure with more than one machine. Whether you're maintaining a cluster of web servers, a set of development VMs, or any group of computers that need consistent configuration, the fleet feature allows you to apply your declarative roles to all of them from a single command.
*   **How is it used?**
    *   **Define your fleet:** In your Ch-obolo file, create a `fleet` key. Inside it, define your `hosts` and their SSH connection details (e.g., `ssh_user`, `ssh_port`, `ssh_key`). You can also set a `parallelism` level to control how many hosts are configured at once.
    *   **Apply to the fleet:** Run your `apply` command with the `--fleet` flag (e.g., `chaos apply packages --fleet`). `chaos` will then connect to each host defined in your fleet via SSH and execute the `packages` role on all of them.

## Plugin System
*   **What is it?** Ch-aOS is built to be minimal and modular. Most of its functionality, including system management tasks ("cores"), command aliases, documentation (`explain`), and even secret provider integrations, is provided through external plugins.
*   **Why use it?** This design means you only install the functionality you need. It also allows the community to extend Ch-aOS for different distributions or add new tools without modifying the central CLI. The CLI is just an engine; the plugins provide the power.
*   **How is it used?**
    *   **Cores:** A "core" is a plugin that provides the basic set of roles for managing a specific Linux distribution (e.g., `ch-aronte` for Arch Linux), these tend to be quite big (In functionality, not in size), as managing different systems do require a LOT of different ways to calculate deltas or even managing different things (for instance, managing an user is as a concept is ALIEN to managing packages).
    *   **Functionality Plugins:** Other plugins can add specialized tools, like `chaos-dots` for dotfile management.
    *   **Secret Providers:** Integrations with password/secret managers like Bitwarden and 1Password are implemented as plugins via the `chaos.providers` entry point, allowing for new providers to be added easily, Ch-aOS comes with these two specific cases from the get-go.
    *   **Discovery:** The `chaos check roles` and `chaos check explanations` commands let you see all the features available from your installed plugins. Run `chaos -u` to update the plugin cache after installing new plugins (sorry for the hassle, its for optimization).

## Integrated Documentation (`chaos explain`)
*   **What is it?** A built-in documentation system that provides detailed (if you so wish) explanations for every feature, command, and concept within Ch-aOS. It's powered by the same plugin system that provides roles, so documentation may even live alongside the functionality it describes, so if you don't want to read about the plugin online, you can just install it and read about it locally, it comes all packaged together!
*   **Why use it?** It offers a didactic and discovery based way to learn Ch-aOS. Instead of just reading a static man page, you can progressively request more detailed information (`--details basic|intermediate|advanced`) on any topic, from high-level concepts to deep technical specifics (and even syntax-highlighted scripts of how to manage your system manually), only on the specific plugins you already have.
*   **How is it used?**
    *   **Explore topics:** Run `chaos check explanations` to see all available documentation topics.
    *   **Get an explanation:** Use `chaos explain <topic>` to read about a feature (e.g., `chaos explain apply`).
    *   **Drill down:** Use `topic.subtopic` to get more specific information (e.g., `chaos explain apply.dry`). You can use `topic.list` to see all available subtopics.
    *   **Increase detail:** Use the `-d` flag to get more advanced information (e.g., `chaos explain secrets.sops -d advanced`), some explanations come baked in, so give it a go!

## Secure Secret Management
*   **What is it?** A suite of commands (`chaos secrets`) that acts as an orchestrator for Mozilla's `sops`. It allows you to safely store sensitive data (like passwords, tokens, and API keys) in encrypted YAML files that can be committed to a Git repository.
*   **Why use it?** It simplifies the entire `sops` workflow, from key rotation to editing encrypted files. It provides a secure way to manage secrets alongside your configuration, ensuring that sensitive values are never exposed in plain text.
*   **How is it used?**
    *   **Initialization:** `chaos init secrets` runs an interactive wizard to set up your encryption keys (`age` or `gpg`) and create your initial `sops` configuration.
    *   **Editing:** `chaos secrets edit` seamlessly decrypts your secrets file into a temporary buffer, opens it in your `$EDITOR`, and automatically re-encrypts it on save.
    *   **Key Management:** `chaos secrets rotate-add` and `rotate-rm` allow you to easily grant or revoke access by adding or removing `age`/`pgp`/`vault` keys from the configuration.
    *   **Access Control:** Use `chaos secrets shamir` to configure an M-of-N policy, requiring a quorum of keys to decrypt a file, enhancing security and redundancy.

## Secret Providers
*   **What are they?** So, you already have your secrets set-up, but... Where do you store your private key?? Well, secret `providers` in Ch-aOS are integrations with external password managers (like Bitwarden and 1Password). They allow the `chaos` CLI to access encryption keys (AGE, GPG, Vault tokens) securely stored in these services, without needing to keep them permanently on the local filesystem (they can even not touch the disk, like ever!)
*   **Why use them?** They provide a significantly enhanced security posture and convenience.
    *   **Ephemeral Keys:** Instead of managing key files on every developer's machine, `chaos` can fetch the necessary decryption keys *ephemerally* (they exist only in memory for the duration of a single command). This approach allows you to manage exactly who, how and when anyone can access your secrets (provided your provider allows for that), while also reducing the attack surface of any given secret!
    *   **Centralized & Auditable Access:** Storing master keys in a password manager provides a central and trusty source. Access can be managed through the password manager's own policies, and in many cases, it is auditable.
    *   **Secure Onboarding:** It simplifies the process of securely distributing keys to new team members. They only need access to the password manager to start decrypting secrets.
*   **How are they used?**
    *   **Configuration:** You can configure default secret providers in the `secret_providers` section of `~/.config/chaos/config.yml`. You can define named providers for specific backends and key types (e.g., `bw.age`).
    *   **Ephemeral Usage:** Many commands that interact with secrets (like `chaos apply`, `secrets edit`, and `ramble read`) accept a `-p` flag to use a provider. For example, `chaos apply users --secrets -p bw.age` will fetch the age key from Bitwarden to decrypt your configured secrets to give to the `users` role. Manual flags for direct item access are also available (`-b` for Bitwarden, `-o` for 1Password, etc. These are given by the plugin, so they will always be available).
    *   **Secure Export/Import:** The `chaos secrets export <provider>` and `import <provider>` commands create a secure workflow for backing up master keys or bootstrapping a new machine.
    *   **Enhanced Export Security (`--no-import`):** When exporting a key with `chaos secrets export`, you can use the `-N` or `--no-import` flag. This embeds a special marker in the secret stored in the password manager. The `chaos secrets import` command will refuse to import any key with this marker. This creates a one-way-trip for a key, allowing it to be distributed for use but preventing it from being extracted from the password manager back to a local file, enforcing a stricter security model where desired. If any plugin doesn't support this feature, you can also just add the marker manually to the secret's notes, the text is, letter for letter "# NO-IMPORT", this can be placed anywhere on the note and Ch-aOS will use it.

## Team Management
*   **What is it?** The team management in Ch-aOS is designed to facilitate collaboration and the sharing of configurations and secrets within a work group. It implements a standard structure for team repositories, allowing members to share `ramblings` (encrypted notes), secret files, and declarative configurations in an organized and secure way.
*   **Why use it?**
    *   **Secure Collaboration:** Allows different team members to access and manage secrets and configurations relevant to their projects, using integrated access control mechanisms (like Shamir's Secret Sharing in SOPS).
    *   **Standardized Structure:** Enforces a directory hierarchy for secrets and `ramblings` (e.g., `secrets/dev`, `secrets/prod`, `ramblings/person`), making organization and understanding easier.
    *   **Clear Workflows:** Offers dedicated commands to initialize, clone, activate, and deactivate team environments, simplifying new member onboarding and project maintenance.
*   **How is it used?**
    *   **Naming Convention:** Teams are identified by a `company.team` convention (e.g., `MyCompany.DevTeam.MyName`). This hierarchy is used to organize files and control access.
    *   **Initialization:** The command `chaos team init MyCompany.DevTeam.MyName` creates a new team repository locally, setting up the directory structure for secrets and `ramblings`, and generating a `sops-config.yml` file tailored for team secret sharing using Shamir's Secret Sharing.
    *   **Cloning and Activation:** Team members can clone an existing team repository (`chaos team clone <REPO_URL>`) or activate an existing one (`chaos team activate [path]`). Activation creates symlinks, registering the team in your local Ch-aOS environment (`~/.local/share/chaos/teams`).
    *   **Deactivation and Pruning:** Commands like `chaos team deactivate` and `chaos team prune` help remove or clean up records of no longer used teams.

## Integrated Knowledge Base (`ramble`)
*   **What is it?** The `ramble` command provides a built-in, file-based personal knowledge base or wiki system. It allows you to create, edit, search, and encrypt notes directly from the command line.
*   **Why use it?** It's a convenient place to store technical notes, documentation, code snippets, and ideas co-located with your system management tools. Since rambles can be encrypted with `sops`, it's also a safe place for sensitive information.
*   **How is it used?**
    *   **Organization:** Notes are organized into "rambles" (directories) and "ramblings" (YAML files) within `~/.local/share/chaos/ramblings/`.
    *   **CRUD Operations:** Use `chaos ramble create journal.page` to make a new note, `edit` to modify it, `read` to view it, and `delete` to remove it.
    *   **Encryption:** A ramble page can be encrypted with `chaos ramble encrypt journal.page`. All subsequent `read` and `edit` operations will handle decryption and re-encryption on their own.
    *   **Search:** The `chaos ramble find` command can perform a case-insensitive search through the content of all your rambles by adding a keyword or sentence at the end of the command, or by a tag inside of a dedicated `tags` field inside of the rambling, by using the `--tag` flag, oh, btw it can find these even if the rambling is encrypted.

### Ideas being studied
- Ch-iron -- a fedora core for Ch-aOS
- Ch-ronos -- a debian core for Ch-aOS
- Mapping for distro agnosticity (probably impossible)
- Direct SSH integration for chaos init and chaos providers, as sops has native integration with it
- chaos.boats entry_point for dinamically discovered fleet definitions from external sources (like chaos providers, but for fleets)
- Ch-imera: a Ch-aOS entry_point for mini ch-obolo-to-nix compilers (this one is going to be my undergrads degree!)

---

# Contributing

Contributions are highly welcomed. If you have ideas to improve Ch-aOS, your help is very welcome! Check out CONTRIBUTING.md to get started.

Areas of particular interest include:

- Suggestions and implementations for post-install configurations.
- Creation of issues.
- Creation of plugins and cores for other distros. These can be very simple, btw, one role at a time can make a true turn of events!!
- Creation of new providers, btw if you create one, PLEASE either 1: put it under GPL/AGPL or 2: create a new PR in this repo, it'd be for the interest of everyone to keep chaos both 1 free and 2 open source (although you CAN always just make it proprietary, either way the more, the merrier)!
- Help with documentation and examples.

