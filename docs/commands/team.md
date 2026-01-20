# Command: `chaos team`

The `team` subsystem provides a structured way to manage and share Ch-aOS configurations (like secrets and rambles) within a team using Git repositories. It enables collaboration by providing a central, version-controlled repository for team-wide settings.

A team repository is a standard Git repository with a specific directory structure (`secrets/`, `ramblings/`) and a `.chaos.yml` file for metadata.

## `team init`

Initializes the standard directory structure and configuration files for a new team repository in the current directory (or a specified path).

**Usage:**
```bash
chaos team init <company.team.person> [path]
```

-   It generates a `.chaos.yml` file defining the team's metadata.

-   It creates a `sops-config.yml` with secure defaults for team secrets (using Shamir's Secret Sharing).

-   It creates the `secrets/` and `ramblings/` directories.

-   It initializes a Git repository if one is not already present.

**Example:**
```bash
# Initialize a repository for a person on a team
chaos team init my-company.my-team.dex

# Initialize in a specific path
chaos team init my-company.my-team.dex ./team-repo
```

## `team clone`

Clones an existing team repository from a Git URL and automatically activates it. This is the standard way for a new team member to join a project.

**Usage:**
```bash
chaos team clone <git_repo_url>
```

It performs a `git clone` and then runs the `activate` logic on the newly cloned directory.

!!! danger
    If the cloned repository does not have a valid `.chaos.yml` file, the activation step will fail, and `chaos` will remove the cloned directory to prevent misconfiguration.

## `team activate`

Registers a local team repository with your Ch-aOS environment. This is useful if you have cloned a repository manually.

**Usage:**
```bash
# Activate the team repo in the current directory
chaos team activate

# Activate a team repo in a specific directory
chaos team activate ./path/to/repo
```

This command reads the `.chaos.yml` file and creates a symlink from `~/.local/share/chaos/teams/<company>/<team>` to your local repository path. This makes the team available for commands like `chaos apply -t my-company.my-team ...`.

## `team deactivate`

Un-registers a team from your local Ch-aOS environment by removing its symlink. This is useful for cleaning up your environment without deleting the repository itself.

**Usage:**
```bash
# Deactivate a specific team
chaos team deactivate <company> <team>

# Deactivate all teams for a company
chaos team deactivate <company>
```

## `team list`

Shows all the teams that are currently activated on your machine.

**Usage:**
```bash
# List all active companies and teams
chaos team list

# List all teams for a specific company
chaos team list <company>
```

## `team prune`

Cleans up your activation directory (`~/.local/share/chaos/teams/`) by removing "stale" symlinks that point to non-existent directories. This is useful if you have manually deleted a team repository from your filesystem without running `deactivate`.

**Usage:**
```bash
chaos team prune
```
