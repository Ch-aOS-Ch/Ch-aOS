class ApplyExplain:
    _order = ["chobolo", "tags", "secrets", "dry"]

    def explain_chobolo(self, detail_level="basic"):
        return {
            "concept": "Ch-obolo: Separation of Data from Logic",
            "what": 'The "Ch-obolo" file is where you declare the desired *data* (what you want your system to be), strictly separate from the *logic* (how to get there).',
            "why": "This clear separation is a fundamental design principle of Ch-aOS. It makes your configurations easier to read, understand, and reuse. It prevents the common pitfall in other automation tools where data and execution flow become intertwined.\nUnlike tools like Ansible, where YAML playbooks often mix variables, tasks, and control flow in a single file, Ch-aOS explicitly separates this. Your Ch-obolo is purely data, and the roles are purely logic.",
            "how": 'Your Ch-obolo file contains simple data structures (YAML) describing users, packages, services, etc. The Python roles (the "logic") then read this data and use Pyinfra operations to apply the changes. The roles themselves contain no hardcoded data about your specific system.',
            "examples": [
                {
                    "yaml": """# The Ch-obolo declares the *data* for a user:
users:
- name: "myuser"
    shell: "zsh"
    sudo: True
"""
                }
            ],
            "technical": "The actual logic for creating this user (e.g., calling `useradd`, `usermod`, configuring sudo) is encapsulated within the `users` Python role, reading the `myuser` data from the Ch-obolo.",
        }

    def explain_apply(self, detail_level="basic"):
        return {
            "concept": "Declarative State Orchestration",
            "what": 'The `apply` command is the engine of Ch-aOS. It reads your Ch-obolo file and executes "roles" to make your system\'s actual state match the desired state you have declared.',
            "why": "It allows you to manage your system in a repeatable, automated, and version-controllable way.",
            "how": "It uses the `pyinfra` library in the background. When you run `chaos apply <tag>`, it finds the role associated with that tag, loads its Python script, and executes the `pyinfra` operations defined within it.",
            "technical": '`pyinfra` first collects "facts" about the current state of the system. It then compares this to the desired state from your Ch-obolo file and calculates a "delta" of operations needed. Finally, it executes those operations.',
            "equivalent": '# Conceptually, this is what happens for a simple role:\n# pyinfra @local my-role.py --sudo --data key="value"\n\n# But pyinfra requires more setup, which chaos apply handles for you.',
            "learn_more": ["pyinfra --help", "Pyinfra Documentation"],
        }

    def explain_tags(self, detail_level="basic"):
        return {
            "concept": "Applying Specific Roles",
            "what": "Tags are the primary mechanism for telling `apply` which specific part of your configuration you want to execute.",
            "why": "They allow you to manage your system modularly. You can apply just the `users` configuration, or just `packages`, or both, without having to run through your entire configuration every time.",
            "how": "When you run `chaos apply users pkgs`, Ch-aOS looks up the roles registered by plugins for the tags `users` and `pkgs` and executes them in order.",
            "examples": [
                {
                    "yaml": """# Apply the configuration for users and packages
    chaos apply users packages

    # You can use aliases defined by plugins
    chaos apply usr pkgs"""
                }
            ],
        }

    def explain_secrets(self, detail_level="basic"):
        return {
            "concept": "Using Secrets in Roles",
            "what": "The `--secrets` flag signals to `chaos apply` that the role you are running needs access to decrypted data from your secrets file.",
            "why": "To securely provide sensitive data, like user passwords or private keys, to your orchestration logic without hardcoding them.",
            "how": "When `--secrets` is present, `chaos` decrypts your secrets file in memory and passes the content to the role function. The role can then access this data to perform its tasks, such as setting a user's password.",
            "security": "The decrypted secrets are only held in memory for the duration of the `apply` command and are not logged.",
            "examples": [
                {
                    "yaml": """# The 'users' role requires passwords, so --secrets is needed
    chaos apply users --secrets

    # Decrypt using an ephemeral key from a configured provider
    chaos apply users --secrets -p bw.age"""
                }
            ],
        }

    def explain_dry(self, detail_level="basic"):
        return {
            "concept": "Dry Run Mode",
            "what": "The `-d` or `--dry` flag tells `chaos apply` to calculate and show all the changes it *would* make, but without actually executing them.",
            "why": "This is an essential safety and learning feature. It allows you to preview and verify the impact of your configuration changes before applying them to your live system.",
            "how": "It passes the `--dry` flag to the underlying `pyinfra` execution engine, which prints a list of proposed operations instead of running them.",
            "equivalent": "pyinfra --dry @local my-role.py",
            "examples": [
                {
                    "yaml": """# See what changes would be made for the 'packages' role
    chaos apply --dry packages

    # Combine with -s and -vvv to get detailed, secret having output
    chaos apply -dsvvv packages
    """
                }
            ],
        }
