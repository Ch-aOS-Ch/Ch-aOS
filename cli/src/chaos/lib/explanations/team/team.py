class TeamExplain:
    _order = ["init", "clone", "activate", "deactivate", "list", "prune"]

    def explain_team(self, detail_level="basic"):
        return {
            "concept": "Team-Based Configuration Management",
            "what": "The `team` subsystem provides a structured way to manage and share Ch-aOS configurations (secrets, rambles) within a team using Git repositories.",
            "why": "It enables collaboration by providing a central, version-controlled repository for team wide settings, while still allowing for personal or group specific overrides.",
            "how": "A team repository is a standard Git repository with a specific directory structure (`secrets/`, `ramblings/`) and a `.chaos.yml` file. The `team` commands help initialize this structure and manage its activation on your local machine via symlinks.",
            "files": ["~/.local/share/chaos/teams/", ".chaos.yml"],
        }

    def explain_init(self, detail_level="basic"):
        return {
            "concept": "Initializing a Team Repository",
            "what": "The `init` command creates the standard directory structure and configuration files for a new team repository in the current directory.",
            "how": "It generates a `.chaos.yml` file that defines the team`s metadata and a `sops-config.yml` with secure defaults for managing team secrets. It also creates the `secrets/` and `ramblings/` directories. It will also initialize a git repository if one is not present.",
            "equivalent": "git init\nmkdir -p secrets ramblings\ntouch .chaos.yml sops-config.yml",
            "examples": [
                {
                    "yaml": "# Initialize a repository for a person on a team\nchaos team init my-company.my-team.dex\n\n# Initialize in a specific path\nchaos team init my-company.my-team.dex ./team-repo"
                }
            ],
        }

    def explain_clone(self, detail_level="basic"):
        return {
            "concept": "Cloning a Team Repository",
            "what": "The `clone` command clones an existing team repository from a Git URL and automatically activates it.",
            "why": "This is the standard way for a new team member to join a project and get all the shared configuration.",
            "how": "It performs a `git clone` and then runs the `activate` logic on the newly cloned directory.",
            "equivalent": "git clone <repo_url>\ncd <repo_name>\nchaos team activate",
            "examples": [
                {
                    "yaml": "chaos team clone git@github.com:my-company/team-chaos-config.git"
                }
            ],
            "security": "If the cloned repository does not have a valid .chaos.yml file, the activation step will fail and remove the cloned directory, ensuring that only properly configured team repositories are activated.",
        }

    def explain_activate(self, detail_level="basic"):
        return {
            "concept": "Activating a Team",
            "what": "The `activate` command registers a local team repository with your Ch-aOS environment.",
            "how": "It reads the `.chaos.yml` file in the target directory and creates a symlink from `~/.local/share/chaos/teams/<company>/<team>` to your local repository path. This makes the team available for commands like `chaos apply -t my-company.my-team ...`.",
            "equivalent": "ln -s /path/to/your/repo ~/.local/share/chaos/teams/my-company/my-team",
            "examples": [
                {
                    "yaml": "# Activate the team repo in the current directory\nchaos team activate\n\n# Activate a team repo in a specific directory\nchaos team activate ./path/to/repo"
                }
            ],
        }

    def explain_deactivate(self, detail_level="basic"):
        return {
            "concept": "Deactivating a Team",
            "what": "The `deactivate` command removes the symlink for a team, effectively un-registering it from your local Ch-aOS environment.",
            "why": "To clean up your environment or switch between different versions of a team configuration without deleting the repository itself.",
            "how": "It finds and removes the corresponding symlink from your `~/.local/share/chaos/teams/` directory.",
            "equivalent": "rm ~/.local/share/chaos/teams/my-company/my-team",
            "examples": [
                {
                    "yaml": "# Deactivate a specific team\nchaos team deactivate my-company my-team\n\n# Deactivate all teams for a company\nchaos team deactivate my-company"
                }
            ],
        }

    def explain_list(self, detail_level="basic"):
        return {
            "concept": "Listing Active Teams",
            "what": "The `list` command shows all the teams that are currently activated on your machine.",
            "how": "It scans the `~/.local/share/chaos/teams/` directory for company and team symlinks and displays them.",
            "equivalent": "ls -l ~/.local/share/chaos/teams/*/*",
            "examples": [
                {
                    "yaml": "# List all active companies and teams\nchaos team list\n\n# List all teams for a specific company\nchaos team list my-company"
                }
            ],
        }

    def explain_prune(self, detail_level="basic"):
        return {
            "concept": "Pruning Stale Teams",
            "what": 'The `prune` command cleans up your activation directory by removing "stale" symlinks.',
            "why": "If you manually delete a team repository from your filesystem without running `deactivate`, the activation symlink becomes a broken link. Pruning removes these dead links.",
            "how": "It checks every symlink in `~/.local/share/chaos/teams/` and removes any that point to a non-existent directory.",
            "equivalent": "find ~/.local/share/chaos/teams -xtype l -delete",
            "examples": [{"yaml": "chaos team prune"}],
        }
