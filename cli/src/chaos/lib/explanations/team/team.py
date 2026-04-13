class TeamExplain:
    _order = ["init", "clone", "activate", "deactivate", "list", "prune"]

    def explain_team(self, complexity="basic"):
        if complexity == "advanced":
            return {
                "concept": "SecretsContext Namespace Resolution",
                "what": "A namespace resolution system for the `SecretsContext`.",
                "how": "When a Payload targets a team (e.g., `team=my.company`), `chaos.lib.teamUtils` resolves the symlink to find the scoped `sops-config.yml` and `ramblings` directory, overriding global paths before execution.",
                "files": ["~/.local/share/chaos/teams/", ".chaos.yml"],
            }
        elif complexity == "intermediate":
            return {
                "concept": "Git-Centric Workspace Manager",
                "what": "A git-centric workspace manager that scopes secrets and documentation to specific groups.",
                "why": "Solves the problem of distributing shared SOPS configurations and encrypted notes without cluttering the global workspace.",
                "how": "Registers repositories via symlinks in `~/.local/share/chaos/teams/`, making them discoverable by the `-t` (team) flag.",
                "files": ["~/.local/share/chaos/teams/", ".chaos.yml"],
            }
        else:
            return {
                "concept": "Team-Based Configuration Management",
                "what": "Provides a structured way to manage and share configurations using Git.",
                "why": "Enables collaboration via a central repository for team-wide settings.",
                "how": "A team repository has `secrets/`, `ramblings/`, and a `.chaos.yml` file. Commands help activate it.",
                "files": ["~/.local/share/chaos/teams/", ".chaos.yml"],
            }

    def explain_init(self, complexity="basic"):
        if complexity == "advanced":
            return {
                "concept": "Workspace Scaffolding via Payload",
                "what": "Constructs a `TeamInitPayload` and uses `handleInitTeam` to scaffold the workspace.",
                "how": "Generates a strict `.chaos.yml` metadata file identifying the namespace, enabling SDK validation during activation.",
                "examples": [
                    {
                        "yaml": "chaos team init my-company.my-team.dex\nchaos team init my-company.my-team.dex ./team-repo"
                    }
                ],
            }
        elif complexity == "intermediate":
            return {
                "concept": "Bootstrapping Team Namespaces",
                "what": "Bootstraps a new team namespace with secure defaults.",
                "how": "Creates the `secrets/` and `ramblings/` directories. Can interactively set up Shamir's Secret Sharing in the generated `.sops.yaml`.",
                "equivalent": "git init\nmkdir -p secrets ramblings\ntouch .chaos.yml sops-config.yml",
                "examples": [{"yaml": "chaos team init my-company.my-team.dex"}],
            }
        else:
            return {
                "concept": "Initializing a Team Repository",
                "what": "Creates the standard directory structure and config files for a new team repository.",
                "how": "Generates `.chaos.yml`, `sops-config.yml`, and initializes a git repository.",
                "equivalent": "git init\nmkdir -p secrets ramblings\ntouch .chaos.yml sops-config.yml",
                "examples": [
                    {
                        "yaml": "chaos team init my-company.my-team.dex\nchaos team init my-company.my-team.dex ./team-repo"
                    }
                ],
            }

    def explain_clone(self, complexity="basic"):
        if complexity == "advanced":
            return {
                "concept": "Payload Execution and Validation",
                "what": "Executes `handleCloneTeam` via `TeamClonePayload`.",
                "how": "Validates the cloned repository against the expected `.chaos.yml` schema. If validation fails, it triggers a rollback, deleting the directory to prevent namespace pollution.",
                "examples": [
                    {
                        "yaml": "chaos team clone git@github.com:my-company/team-chaos-config.git"
                    }
                ],
            }
        elif complexity == "intermediate":
            return {
                "concept": "Automated Retrieval and Registration",
                "what": "Automates the retrieval and registration of a team workspace.",
                "why": "Ensures the repository is placed in the correct location and immediately symlinked for `chaos` to discover.",
                "how": "Wraps `git clone` via subprocess, then executes the internal `team activate` function on the resulting directory.",
                "equivalent": "git clone <repo_url>\ncd <repo_name>\nchaos team activate",
                "examples": [
                    {
                        "yaml": "chaos team clone git@github.com:my-company/team-chaos-config.git"
                    }
                ],
            }
        else:
            return {
                "concept": "Cloning a Team Repository",
                "what": "Clones an existing team repository from a Git URL and automatically activates it.",
                "why": "The standard way for a new team member to join a project.",
                "how": "Performs a `git clone` and then runs the `activate` logic.",
                "equivalent": "git clone <repo_url>\ncd <repo_name>\nchaos team activate",
                "security": "If the cloned repository does not have a valid .chaos.yml file, the activation step will fail.",
                "examples": [
                    {
                        "yaml": "chaos team clone git@github.com:my-company/team-chaos-config.git"
                    }
                ],
            }

    def explain_activate(self, complexity="basic"):
        if complexity == "advanced":
            return {
                "concept": "Symlink Tree Atomic Creation",
                "what": "Executes `handleActivateTeam` using `TeamActivatePayload`.",
                "how": "Ensures atomicity when creating the symlink tree. Handles edge cases where existing broken links or differing namespaces might cause conflicts.",
                "examples": [
                    {"yaml": "chaos team activate\nchaos team activate ./path/to/repo"}
                ],
            }
        elif complexity == "intermediate":
            return {
                "concept": "Namespace Routing Registration",
                "what": "Creates the namespace routing symlink for the Ch-aOS context resolver.",
                "how": "Reads the `namespace` attribute from `.chaos.yml` and creates a symlink tree (e.g., `company/team`) pointing to the current working directory.",
                "equivalent": "ln -s /path/to/your/repo ~/.local/share/chaos/teams/my-company/my-team",
                "examples": [
                    {"yaml": "chaos team activate\nchaos team activate ./path/to/repo"}
                ],
            }
        else:
            return {
                "concept": "Activating a Team",
                "what": "Registers a local team repository with your Ch-aOS environment.",
                "how": "Creates a symlink from `~/.local/share/chaos/teams/` to your local repository path.",
                "equivalent": "ln -s /path/to/your/repo ~/.local/share/chaos/teams/my-company/my-team",
                "examples": [
                    {"yaml": "chaos team activate\nchaos team activate ./path/to/repo"}
                ],
            }

    def explain_deactivate(self, complexity="basic"):
        if complexity == "advanced":
            return {
                "concept": "Payload Execution for Deactivation",
                "what": "Executes `handleDeactivateTeam` using `TeamDeactivatePayload`.",
                "how": "Performs safe `os.unlink` operations. If deactivating a top-level namespace (e.g., the company), it recursively removes all sub-team links.",
                "examples": [
                    {
                        "yaml": "chaos team deactivate my-company my-team\nchaos team deactivate my-company"
                    }
                ],
            }
        elif complexity == "intermediate":
            return {
                "concept": "Namespace Routing Destruction",
                "what": "Destroys the namespace routing symlink.",
                "why": "Useful when switching contexts or abandoning a workspace locally.",
                "how": "Traverses the `teams/` directory and unlinks the specified namespace path.",
                "equivalent": "rm ~/.local/share/chaos/teams/my-company/my-team",
                "examples": [
                    {
                        "yaml": "chaos team deactivate my-company my-team\nchaos team deactivate my-company"
                    }
                ],
            }
        else:
            return {
                "concept": "Deactivating a Team",
                "what": "Removes the symlink for a team, un-registering it.",
                "why": "To clean up your environment without deleting the repository itself.",
                "how": "Finds and removes the symlink from `~/.local/share/chaos/teams/`.",
                "equivalent": "rm ~/.local/share/chaos/teams/my-company/my-team",
                "examples": [
                    {
                        "yaml": "chaos team deactivate my-company my-team\nchaos team deactivate my-company"
                    }
                ],
            }

    def explain_list(self, complexity="basic"):
        if complexity == "advanced":
            return {
                "concept": "Programmatic Namespace Enumeration",
                "what": "Executes `handleListTeam` via `TeamListPayload`.",
                "how": "Returns a structured dictionary of namespaces mapped to physical paths on disk, allowing SDK users to programmatically enumerate team contexts.",
                "examples": [{"yaml": "chaos team list\nchaos team list my-company"}],
            }
        elif complexity == "intermediate":
            return {
                "concept": "Resolved Namespace Display",
                "what": "Displays the resolved namespaces currently recognized by the context resolver.",
                "how": "Iterates through the symlink tree in `~/.local/share/chaos/teams/` and resolves their absolute paths to display to the user.",
                "equivalent": "ls -l ~/.local/share/chaos/teams/*/*",
                "examples": [{"yaml": "chaos team list\nchaos team list my-company"}],
            }
        else:
            return {
                "concept": "Listing Active Teams",
                "what": "Shows all the teams that are currently activated on your machine.",
                "how": "Scans the `teams/` directory for symlinks and displays them.",
                "equivalent": "ls -l ~/.local/share/chaos/teams/*/*",
                "examples": [{"yaml": "chaos team list\nchaos team list my-company"}],
            }

    def explain_prune(self, complexity="basic"):
        if complexity == "advanced":
            return {
                "concept": "Payload-Driven Pruning",
                "what": "Executes `handlePruneTeam` via `TeamPrunePayload`.",
                "how": "Ensures the `SecretsContext` resolver does not fail on dangling pointers. Returns a list of pruned namespaces in `ResultPayload.data`.",
                "examples": [{"yaml": "chaos team prune"}],
            }
        elif complexity == "intermediate":
            return {
                "concept": "Garbage Collection for Routing Table",
                "what": "A garbage collection routine for the namespace routing table.",
                "how": "Validates the existence of the target path (`os.path.exists`) for every symlink in the `teams/` tree. If false, `os.unlink` is called.",
                "equivalent": "find ~/.local/share/chaos/teams -xtype l -delete",
                "examples": [{"yaml": "chaos team prune"}],
            }
        else:
            return {
                "concept": "Pruning Stale Teams",
                "what": "Cleans up your activation directory by removing 'stale' symlinks.",
                "why": "Fixes broken links if you manually deleted a team repository.",
                "how": "Checks every symlink and removes any that point to a non-existent directory.",
                "equivalent": "find ~/.local/share/chaos/teams -xtype l -delete",
                "examples": [{"yaml": "chaos team prune"}],
            }
