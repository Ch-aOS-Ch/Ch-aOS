class ApplyExplain:
    _order = ["chobolo", "tags", "secrets", "dry"]

    def explain_chobolo(self, complexity="basic"):
        if complexity == "advanced":
            return {
                "concept": "Ch-obolo: Data Segregation and Injection",
                "what": "The Ch-obolo is parsed into an OmegaConf DictConfig and injected into the ApplyPayload.",
                "why": "It enables deterministic state reconciliation by decoupling the system state from execution logic. Roles use this decoupled data to compute a precise Delta.",
                "how": "During execution, `chaos.lib.apply` loads the YAML. When `get_context` and `delta` are called on a Role, this data dictates the Pyinfra operations.",
                "examples": [
                    {
                        "yaml": """# ch-obolo.yml
users:
- name: "myuser"
  shell: "zsh"
  sudo: True"""
                    }
                ]
            }
        elif complexity == "intermediate":
            return {
                "concept": "Ch-obolo: Configuration Data",
                "what": "A YAML file acting as the single source of truth for the system state, strictly separated from execution logic.",
                "why": "It makes configurations modular and reusable. Your Ch-obolo is purely data, and the Python roles are purely logic.",
                "how": "Python roles read this data to understand what needs to be changed, generating the specific commands to apply those changes.",
                "examples": [
                    {
                        "yaml": """# ch-obolo.yml
users:
- name: "myuser"
  shell: "zsh"
  sudo: True"""
                    }
                ]
            }
        else:
            return {
                "concept": "Ch-obolo: Separation of Data from Logic",
                "what": 'The "Ch-obolo" file is where you declare the desired *data* (what you want your system to be), strictly separate from the *logic* (how to get there).',
                "why": "This clear separation makes your configurations easier to read, understand, and reuse.",
                "how": 'Your Ch-obolo file contains simple data structures (YAML) describing users, packages, services, etc.',
                "examples": [
                    {
                        "yaml": """# The Ch-obolo declares the *data* for a user:
users:
- name: "myuser"
  shell: "zsh"
  sudo: True"""
                    }
                ]
            }

    def explain_apply(self, complexity="basic"):
        if complexity == "advanced":
            return {
                "concept": "State Reconciliation Engine",
                "what": "The core orchestrator that constructs an `ApplyPayload`, initializes Pyinfra, and executes the `Context -> Delta -> Plan` lifecycle.",
                "why": "It enforces strict atomicity and captures exact commands, facts, and timings into the Logbook for telemetry and debugging.",
                "how": "The SDK runs `gather_apply`, sets up the `pyinfra_state`, and loops through hosts. For each role, it calls `get_context()`, then `delta()`, and `plan()` to stage operations in Pyinfra's Topological Sorter before execution.",
                "equivalent": "chaos.lib.apply.execute_plans(payload)",
                "learn_more": ["pyinfra --help", "Pyinfra Documentation"],
            }
        elif complexity == "intermediate":
            return {
                "concept": "Declarative Execution",
                "what": "`apply` triggers the reconciliation loop, executing roles to match the system's state to your Ch-obolo.",
                "why": "It abstracts Pyinfra's complexity, providing a version-controllable and repeatable system management process.",
                "how": "It loads Python role scripts, collects facts about the system, calculates the difference (delta), and executes the necessary commands.",
                "equivalent": '# pyinfra @local my-role.py --sudo --data key="value"',
                "learn_more": ["pyinfra --help", "Pyinfra Documentation"],
            }
        else:
            return {
                "concept": "Declarative State Orchestration",
                "what": 'The `apply` command is the engine of Ch-aOS. It reads your Ch-obolo file and executes "roles" to make your system\'s actual state match the desired state.',
                "why": "It allows you to manage your system in a repeatable, automated way.",
                "how": "It uses the `pyinfra` library in the background to execute operations defined within roles.",
                "learn_more": ["pyinfra --help", "Pyinfra Documentation"],
            }

    def explain_tags(self, complexity="basic"):
        if complexity == "advanced":
            return {
                "concept": "Plugin Entry Point Resolution",
                "what": "Identifiers used to resolve `chaos.roles` entry points into Role class instances during the `gather_apply` phase.",
                "why": "They determine which parts of the execution graph are built and which `necessary_chobolo_keys` are validated against the OmegaConf configuration.",
                "how": "The Payload `tags` attribute is populated, aliases are resolved via `resolve_aliases`, and corresponding Role plugins are dynamically imported.",
                "examples": [{"yaml": "chaos apply users packages\nchaos apply usr pkgs"}]
            }
        elif complexity == "intermediate":
            return {
                "concept": "Role Execution Filtering",
                "what": "Tags map to specific Role classes registered by plugins, dictating which logic blocks are evaluated.",
                "why": "It avoids running the entire system configuration every time, speeding up updates and minimizing risk.",
                "how": "Ch-aOS looks up plugins matching the tags (or aliases in `chaos.aliases`) and executes them sequentially.",
                "examples": [{"yaml": "chaos apply users packages\nchaos apply usr pkgs"}]
            }
        else:
            return {
                "concept": "Applying Specific Roles",
                "what": "Tags are the primary mechanism for telling `apply` which specific part of your configuration you want to execute.",
                "why": "They allow you to apply just the `users` configuration, or just `packages`, without running everything.",
                "how": "Run `chaos apply <tags>` to execute only those parts.",
                "examples": [{"yaml": "chaos apply users packages\nchaos apply usr pkgs"}]
            }

    def explain_secrets(self, complexity="basic"):
        if complexity == "advanced":
            return {
                "concept": "Ephemeral SecretsContext Injection",
                "what": "Triggers the population of a `SecretsContext` within the `ApplyPayload`, utilizing `chaos.lib.secret_backends` to inject an OmegaConf Dict into the Role lifecycle.",
                "why": "To achieve a highly secure, ephemeral secret injection pipeline. It supports integrating with IAM/Vault providers to decrypt SOPS files securely.",
                "how": "During SDK setup, `decrypt_secrets` is called. It fetches keys, invokes SOPS decryption in-memory, and immediately wipes the key. The Dict is passed to the Role's methods.",
                "security": "Keys are held in tmpfs or secure memory pipes for milliseconds during the SOPS subprocess invocation."
            }
        elif complexity == "intermediate":
            return {
                "concept": "In-Memory Secret Decryption",
                "what": "Initiates an in-memory decryption of your SOPS file, injecting the data into the role's context.",
                "why": "Ensures passwords and API keys are never written to disk unencrypted, while being fully available for templating.",
                "how": "`chaos` reads `sops-config.yml`, uses the appropriate master key, decrypts the file, and passes the resulting dictionary to the Role.",
                "examples": [{"yaml": "chaos apply users --secrets\nchaos apply users --secrets -p bw.age"}]
            }
        else:
            return {
                "concept": "Using Secrets in Roles",
                "what": "The `--secrets` flag signals that the role needs access to decrypted data from your secrets file.",
                "why": "To securely provide sensitive data without hardcoding it.",
                "how": "`chaos` decrypts your secrets file in memory and passes the content to the role.",
                "security": "The decrypted secrets are only held in memory for the duration of the command.",
                "examples": [{"yaml": "chaos apply users --secrets\nchaos apply users --secrets -p bw.age"}]
            }

    def explain_dry(self, complexity="basic"):
        if complexity == "advanced":
            return {
                "concept": "Pyinfra Graph Evaluation (Dry Run)",
                "what": "Modifies the `ApplyPayload.dry` boolean, instructing the Pyinfra executor to halt after the Topological Sorter has built the operation graph.",
                "why": "Provides a safe way to test `delta()` logic and `get_context()` fact gathering of SDK Roles without side-effects.",
                "how": "Roles fully evaluate, calculate Deltas, and stage operations. Pyinfra skips the `execute_plans` step, instead yielding the diffs to stdout and the Logbook.",
                "equivalent": "pyinfra --dry @local my-role.py",
                "examples": [{"yaml": "chaos apply --dry packages\nchaos apply -dsvvv packages"}]
            }
        elif complexity == "intermediate":
            return {
                "concept": "Execution Plan Calculation",
                "what": "Calculates and displays the Pyinfra execution plan without applying state changes to the target hosts.",
                "why": "Allows you to verify the calculated changes and ensure your configuration has the exact intended impact.",
                "how": "Passes `--dry` down to Pyinfra. Pyinfra collects facts, roles stage their operations, and it prints the diffs without executing shell commands.",
                "examples": [{"yaml": "chaos apply --dry packages\nchaos apply -dsvvv packages"}]
            }
        else:
            return {
                "concept": "Dry Run Mode",
                "what": "The `-d` or `--dry` flag shows what changes *would* be made, without actually executing them.",
                "why": "It's an essential safety feature to preview your changes before applying them to your live system.",
                "how": "It prints a list of proposed operations instead of running them.",
                "examples": [{"yaml": "chaos apply --dry packages\nchaos apply -dsvvv packages"}]
            }
