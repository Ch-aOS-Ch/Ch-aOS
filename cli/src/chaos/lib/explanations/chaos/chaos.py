class ChaosExplain:
    _order = ["chobolo", "set", "init", "check"]

    def explain_chaos(self, detail_level="basic"):
        return {
            "concept": "The Ch-aOS Command-Line Interface",
            "what": "`chaos` is the main entry point for the Ch-aOS tool. It acts as a CLI to orchestrate system configuration, manage secrets, and handle team Ch-aOS configurations and documentation.",
            "why": "It provides a single interface to some backend tools (like `pyinfra` and `sops`), simplifying complex workflows and making system management declarative and repeatable (I'M WORKING ON ATOMICITY OK?).",
            "how": 'When you run a command like `chaos apply users -s`, the CLI parses your arguments, loads the necessary configuration from your "Ch-obolo" file, discovers the appropriate role from its plugins, and executes the underlying logic.',
            "learn_more": ["run `chaos --help` to see all available commands."],
        }

    def explain_chobolo(self, detail_level="basic"):
        return {
            "concept": 'The "Ch-obolo" Configuration File',
            "what": 'A "Ch-obolo" is a YAML file that serves as the central source of truth for declaring the desired state of a system. It contains all the variables and data that the different roles (like `users` or `packages`) will use.',
            "why": "It allows you to define your entire system configuration in a single, human-readable, version-controllable file.",
            "how": "You specify which Ch-obolo file to use with the `-c` flag (e.g., `chaos apply -c my-config.yml ...`) or by setting a default path with `chaos set chobolo`. The roles you apply will then read their configuration from this file.",
            "examples": [
                {
                    "yaml": """# ch-obolo.yml
hostname: "my-arch-box"

users:
  - name: "dex"
    shell: "zsh"
    sudo: True
    groups:
      - wheel
      - docker

# Then run chaos apply users
"""
                }
            ],
        }

    def explain_set(self, detail_level="basic"):
        return {
            "concept": "Setting Default File Paths",
            "what": "The `chaos set` command allows you to configure default paths for your most used files, so you don't have to specify them with flags on every command.",
            "why": "It improves convenience by saving you from repeatedly typing file paths for your main Ch-obolo, secrets, or sops configuration files.",
            "how": "It saves the provided file paths to a central chaos configuration file located at `~/.config/chaos/config.yml`.",
            "equivalent": 'echo "chobolo_file: /path/to/your/ch-obolo.yml" > ~/.config/chaos/config.yml',
            "examples": [
                {
                    "yaml": """# Set the default chobolo file
chaos set chobolo ~/configs/main-chobolo.yml

# Set the default secrets and sops files
chaos set secrets ~/secrets/my-secrets.sops.yml
chaos set sops ~/secrets/.sops.yaml"""
                }
            ],
            "files": ["~/.config/chaos/config.yml"],
        }

    def explain_init(self, detail_level="basic"):
        return {
            "concept": "Project Initialization",
            "what": "The `chaos init` command is a setup wizard that creates boilerplate configuration files for you.",
            "why": "It lowers the barrier to entry by generating template files, saving you from having to write them from scratch.",
            "how": "It offers currently the subcommands `chobolo` and `secrets`. `init chobolo` scans your installed plugins for configuration keys and generates a template Ch-obolo file. `init secrets` walks you through setting up `sops` with `age` or `gpg`.",
            "examples": [
                {
                    "yaml": """# Create a boilerplate chobolo file based on installed plugins
chaos init chobolo

# Start the interactive wizard to create sops and secrets files
chaos init secrets"""
                }
            ],
        }

    def explain_check(self, detail_level="basic"):
        return {
            "concept": "Configuration Auditing",
            "what": "The `chaos check` command allows you to list the available components that Ch-aOS can use.",
            "why": "It helps you discover what functionality is available from your installed core components and plugins.",
            "how": "It can list all available `roles`, `aliases`, and `explanations` that have been registered through the plugin system.",
            "examples": [
                {
                    "yaml": """# List all available roles you can use with 'chaos apply'
chaos check roles

# List all available command aliases
chaos check aliases

# List all topics you can read about with 'chaos explain'
chaos check explanations"""
                }
            ],
            "files": ["/usr/share/chaos/plugins/", "~/.local/share/chaos/plugins/"],
        }
