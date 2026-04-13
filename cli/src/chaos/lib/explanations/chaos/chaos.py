class ChaosExplain:
    _order = ["chobolo", "set", "init", "check"]

    def explain_chaos(self, complexity="basic"):
        if complexity == "advanced":
            return {
                "concept": "Ch-aOS SDK Wrapper",
                "what": "A CLI layer that instantiates optimized Data Transfer Objects (Payloads) and dispatches them to the core API-first Ch-aOS SDK.",
                "why": "It ensures that all functionality available in the CLI is equally accessible programmatically for custom automation or CI/CD pipelines.",
                "how": "Uses `argparse` to build Payloads, handles interactive prompts via `gather_*` functions, and passes constructed Payloads to `handle_*` execution methods.",
                "learn_more": ["run `chaos --help` to see all available commands."],
            }
        elif complexity == "intermediate":
            return {
                "concept": "Ch-aOS Command Orchestrator",
                "what": "The CLI wrapper orchestrating `pyinfra`, `sops`, and a modular plugin ecosystem.",
                "why": "It provides a unified interface to achieve declarative system management, secret decryption, and documentation management.",
                "how": "It translates user commands into parameters that drive SDK execution, managing the lifecycle of configuration and plugin loading.",
                "learn_more": ["run `chaos --help` to see all available commands."],
            }
        else:
            return {
                "concept": "The Ch-aOS Command-Line Interface",
                "what": "`chaos` is the main entry point for the Ch-aOS tool. It manages system configuration, secrets, and team documentation.",
                "why": "It simplifies complex workflows and makes system management declarative and repeatable.",
                "how": "When you run a command, the CLI parses your arguments, loads configuration, and executes the underlying logic.",
                "learn_more": ["run `chaos --help` to see all available commands."],
            }

    def explain_chobolo(self, complexity="basic"):
        if complexity == "advanced":
            return {
                "concept": "OmegaConf DictConfig Injection",
                "what": "The Ch-obolo is parsed using `OmegaConf` into a `DictConfig` object, providing advanced features like variable interpolation.",
                "why": "OmegaConf allows for dynamic configuration injection, fleet definitions, and schema validation during the SDK's execution cycle.",
                "how": "The SDK loads the YAML, merges it with global configurations, and passes it into the Role's `get_context()` method to compute Deltas.",
                "examples": [
                    {
                        "yaml": """# ch-obolo.yml
hostname: "my-arch-box"
users:
  - name: "dex"
    shell: "zsh"
    sudo: True"""
                    }
                ]
            }
        elif complexity == "intermediate":
            return {
                "concept": "Configuration Source of Truth",
                "what": "A data-only YAML file containing variables used by Ch-aOS roles, keeping logic decoupled from data.",
                "why": "It makes your infrastructure code modular. You can use the same roles across different machines simply by providing a different Ch-obolo.",
                "how": "Roles declare required keys. `chaos apply` reads the Ch-obolo and provides this data to the roles during execution.",
                "examples": [
                    {
                        "yaml": """# ch-obolo.yml
hostname: "my-arch-box"
users:
  - name: "dex"
    shell: "zsh"
    sudo: True"""
                    }
                ]
            }
        else:
            return {
                "concept": 'The "Ch-obolo" Configuration File',
                "what": 'A YAML file that serves as the central source of truth for declaring the desired state of a system.',
                "why": "It allows you to define your entire system configuration in a single, human-readable file.",
                "how": "You specify which Ch-obolo file to use with the `-c` flag or `chaos set chobolo`.",
                "examples": [
                    {
                        "yaml": """# ch-obolo.yml
hostname: "my-arch-box"
users:
  - name: "dex"
    shell: "zsh"
    sudo: True"""
                    }
                ]
            }

    def explain_set(self, complexity="basic"):
        if complexity == "advanced":
            return {
                "concept": "Global Configuration Mutation",
                "what": "Constructs a `SetPayload` to programmatically update the global OmegaConf configuration dictionary.",
                "why": "Provides an automated way to bootstrap environments and defaults before launching full SDK orchestrations.",
                "how": "The `chaos.lib.set.handleSet` function reads the existing global config, applies mutated values, and serializes it back to disk.",
                "files": ["~/.config/chaos/config.yml"],
                "examples": [{"yaml": "chaos set chobolo ~/configs/main-chobolo.yml\nchaos set secrets ~/configs/secrets.sops.yml"}]
            }
        elif complexity == "intermediate":
            return {
                "concept": "Updating Default Targets",
                "what": "Updates the global `config.yml` to persist default targets for operations like `apply` or `secrets`.",
                "why": "Improves CLI ergonomics by setting a primary default context for your workspace.",
                "how": "It modifies the YAML structure of `~/.config/chaos/config.yml`, setting `chobolo_file`, `secrets_file`, or `sops_file`.",
                "equivalent": "echo \"chobolo_file: ...\" > ~/.config/chaos/config.yml",
                "files": ["~/.config/chaos/config.yml"],
                "examples": [{"yaml": "chaos set chobolo ~/configs/main-chobolo.yml"}]
            }
        else:
            return {
                "concept": "Setting Default File Paths",
                "what": "The `chaos set` command configures default paths for your most used files.",
                "why": "It saves you from repeatedly typing file paths on every command.",
                "how": "It saves the paths to a central config file at `~/.config/chaos/config.yml`.",
                "files": ["~/.config/chaos/config.yml"],
                "examples": [{"yaml": "chaos set chobolo ~/configs/main-chobolo.yml"}]
            }

    def explain_init(self, complexity="basic"):
        if complexity == "advanced":
            return {
                "concept": "Dynamic SDK Bootstrapping",
                "what": "Uses `chaos.lib.inits` to dynamically construct configuration states based on the active plugin registry.",
                "why": "Ensures initialized environments adhere to schemas expected by the SDK's Roles and Secret handlers.",
                "how": "Constructs an `InitPayload`. For SOPS, it utilizes `gatherInitSecrets` to build the required `DataGatherRequest`, then writes configuration to disk.",
                "examples": [{"yaml": "chaos init chobolo\nchaos init secrets"}]
            }
        elif complexity == "intermediate":
            return {
                "concept": "Environment Scaffold Generation",
                "what": "A command suite generating Ch-obolos based on installed plugins or configuring SOPS defaults.",
                "why": "Automates the creation of `.sops.yaml` rules and discovers required keys from all installed roles.",
                "how": "For `chobolo`, it aggregates the `chaos.keys` entry points. For `secrets`, it guides GPG/Age master key selection.",
                "examples": [{"yaml": "chaos init chobolo\nchaos init secrets"}]
            }
        else:
            return {
                "concept": "Project Initialization",
                "what": "The `chaos init` command is a setup wizard that creates boilerplate configuration files.",
                "why": "It lowers the barrier to entry by generating template files for you.",
                "how": "`init chobolo` generates a template Ch-obolo file. `init secrets` walks you through setting up `sops`.",
                "examples": [{"yaml": "chaos init chobolo\nchaos init secrets"}]
            }

    def explain_check(self, complexity="basic"):
        if complexity == "advanced":
            return {
                "concept": "Plugin Registry Introspection",
                "what": "Constructs a `CheckPayload` and utilizes `chaos.lib.checkers` to introspect the SDK's plugin registry.",
                "why": "Crucial for programmatic discovery, allowing interfaces or scripts to dynamically adapt to installed plugins.",
                "how": "The SDK parses `entry_points` groups (like `chaos.roles` or `chaos.boats`), attempts to load them to verify integrity, and returns the registry map.",
                "files": ["/usr/share/chaos/plugins/", "~/.local/share/chaos/plugins/"],
                "examples": [{"yaml": "chaos check roles"}]
            }
        elif complexity == "intermediate":
            return {
                "concept": "Active Component Auditing",
                "what": "Audits and lists dynamically loaded plugins and entry points currently active in the Ch-aOS environment.",
                "why": "Useful for verifying plugin installations and understanding available tags/aliases before running an `apply`.",
                "how": "Queries the Python `importlib.metadata` system to find all packages exporting `chaos.*` entry points.",
                "files": ["/usr/share/chaos/plugins/", "~/.local/share/chaos/plugins/"],
                "examples": [{"yaml": "chaos check roles\nchaos check aliases\nchaos check explanations"}]
            }
        else:
            return {
                "concept": "Configuration Auditing",
                "what": "The `chaos check` command allows you to list the available components that Ch-aOS can use.",
                "why": "It helps you discover what functionality is available from your installed core components and plugins.",
                "how": "It can list all available `roles`, `aliases`, and `explanations`.",
                "files": ["/usr/share/chaos/plugins/", "~/.local/share/chaos/plugins/"],
                "examples": [{"yaml": "chaos check roles\nchaos check aliases\nchaos check explanations"}]
            }
