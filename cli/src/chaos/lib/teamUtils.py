from chaos.lib.utils import checkDep
from omegaconf import DictConfig, OmegaConf
from typing import cast
from rich.prompt import Prompt, Confirm
from rich.panel import Panel
from pathlib import Path
import yaml
import os
from rich.console import Console
import sys

console = Console()

def _validate_deps():
    hasAge = checkDep('age-keygen')
    hasSops = checkDep('sops')
    hasPgp = checkDep('gpg')

    if not hasSops:
        console.print("[bold red]CRITICAL:[/] sops is not installed. It is required for this software.")
        sys.exit(1)

    if not (hasAge or hasPgp):
        console.print("[bold red]CRITICAL:[/] Neither gpg nor age are installed. At least one is required for this functionality.")
        sys.exit(1)

    return hasAge, hasPgp

def _symlink_teamDir(company: str, base_path: Path, team: str):
    try:
        src = base_path / company / team
        dest = Path(f"~/.local/share/chaos/teams/{company}/{team}").expanduser()

        dest.parent.mkdir(parents=True, exist_ok=True)

        if dest.is_symlink():
            if dest.resolve() == src.resolve():
                console.print(f"[bold green]Success![/] Team [bold]{team}[/] from company [bold]{company}[/] is already active.")
                return
            else:
                console.print(f"[bold red]ERROR:[/] Another project for team '{team}' in company '{company}' is already active from a different path.")
                sys.exit(1)
        elif dest.exists():
            console.print(f"[bold red]ERROR:[/] A file or directory already exists at the activation path: {dest}")
            sys.exit(1)

        dest.symlink_to(src, target_is_directory=True)

        console.print(f"[bold green]Success![/] Team [bold]{team}[/] from company [bold]{company}[/] activated at [dim]{dest}[/]")
    except Exception as e:
        console.print(f"[bold red]ERROR:[/] Failed to activate team: {e}")
        sys.exit(1)

def _validate_paths(args):
    batch = args.target

    parts = batch.split('.')
    company = parts[0]
    team = parts[1]
    person = parts[2] if len(parts) == 3 else None

    if not '.' in batch:
        Console().print("[bold red]ERROR:[/] Must set a company for your team. (company.team.person)")
        sys.exit(1)
    if not team or not company:
        console.print("[bold red]ERROR:[/] Must pass both team and company.")
        sys.exit(1)

    if person:
        if ".." in person or person.startswith("/"):
            console.print(f"[bold red]ERROR:[/] Invalid group name '{person}'.")
            sys.exit(1)

    if ".." in company or company.startswith("/"):
         console.print(f"[bold red]ERROR:[/] Invalid company name '{company}'.")
         sys.exit(1)

    if ".." in team or team.startswith("/"):
         console.print(f"[bold red]ERROR:[/] Invalid team name '{team}'.")
         sys.exit(1)

    return company, team, person

def _create_chaos_file(path, company: str, team: str, person: str|None, engine: str):
    chaos_file = Path(os.path.join(os.getcwd())) / ".chaos.yml" if not path else Path(path) / ".chaos.yml"
    if not chaos_file.exists():
        chaosContent = {
            "company": company,
            "teams": [team],
            "people": [person] if person else [],
            "engine": [engine] if engine != "both" else ["age", "gpg"]
        }
        yaml.dump(chaosContent, open(chaos_file, 'w'), default_flow_style=False)

def _get_chaos_file(path) -> DictConfig:
    chaos_file = Path(os.path.join(os.getcwd())) / ".chaos.yml" if not path else Path(path) / ".chaos.yml"
    if not chaos_file.exists():
        console.print("[bold red]ERROR:[/] No .chaos.yml file found in current directory.")
        sys.exit(1)

    chaosContent = OmegaConf.load(chaos_file)
    chaosContent = cast(DictConfig, chaosContent)
    if not chaosContent.company or not chaosContent.team or not chaosContent.engine:
        console.print("[bold red]ERROR:[/] .chaos.yml file is missing required fields (company, team, engine).")
        sys.exit(1)

    return chaosContent

def _create_sops_config(teamDir, hasAge: bool, choices: list[str], person: str|None, ikwid) -> str:
    sops_file = teamDir / "sops-config.yml"
    if sops_file.exists():
        if not Confirm.ask(f"A sops configuration already exists at [dim]{sops_file}[/]. Overwrite?", default=False):
            console.print("[yellow]Operation cancelled. Keeping existing config.[/]")
            sys.exit(0)

    default="age" if hasAge else "gpg"
    console.print(Panel("Chaos uses [bold]SOPS[/] for encryption.\nYou need to choose a backend engine to handle the keys.", title="Secrets Initialization", border_style="green"))
    engine = "age" if ikwid else Prompt.ask("Choose encryption engine", choices=choices, default=default)

    dev_key_groups = []
    prod_key_groups = []
    ramblings_key_groups = []

    hasVault = checkDep('vault')

    if hasVault:
        useVault = True if ikwid else Confirm.ask("Do you wish to use vault? (recommended for security)", default=True)
        if useVault:
            dev_key_groups.extend([
                { "hc_vault": [ "VAULT-TEAM-URI-INSTANCE." ] },
                { "hc_vault": [ "VAULT-COMPANY-URI-INSTANCE" ] }
            ])
            prod_key_groups.extend([
                { "hc_vault": [ "VAULT-TEAM-URI-INSTANCE." ] },
                { "hc_vault": [ "VAULT-COMPANY-URI-INSTANCE" ] },
                { "hc_vault": [ "VAULT-SECURITY-TEAM-URI-INSTANCE" ] },
                { "hc_vault": [ "VAULT-COMPLIANCE-TEAM-URI-INSTANCE" ] }
            ])
            ramblings_key_groups.extend([
                { "hc_vault": [ "VAULT-TEAM-URI-INSTANCE." ] },
                { "hc_vault": [ "VAULT-COMPANY-URI-INSTANCE" ] }
            ])
    else:
        console.print("[bold yellow]WARNING:[/] Vault is not installed. Using vault is the more secure way to manage your secrets.")
        confirm = Confirm.ask("Do you wish to continue without vault?", default=False)
        if not confirm:
            console.print("Operation cancelled. Please install vault and try again.")
            sys.exit(1)

    if engine in ["gpg", "both"]:
        dev_key_groups.extend([
            { "pgp": [ "YOUR-TEAM-UNIFIED-PGP-KEYS" ] },
            { "pgp": [ "BACKUP-PGP-KEYS" ] }
        ])
        prod_key_groups.extend([
            { "pgp": [ "EACH-OF-YOUR-TEAM-MEMBERS-PGP-KEYS" ] },
            { "pgp": [ "BACKUP-PGP-KEYS" ] }
        ])
        ramblings_key_groups.extend([
            { "pgp": [ "YOUR-TEAM-MEMBER-PGP-KEY" ] },
            { "pgp": [ "BACKUP-PGP-KEYS" ] }
        ])

    if engine in ["age", "both"]:
        dev_key_groups.extend([
            { "age": [ "YOUR-TEAM-UNIFIED-AGE-KEYS" ] },
            { "age": [ "BACKUP-AGE-KEYS" ] }
        ])
        prod_key_groups.extend([
            { "age": [ "EACH-OF-YOUR-TEAM-MEMBERS-AGE-KEYS" ] },
            { "age": [ "BACKUP-AGE-KEYS" ] }
        ])
        ramblings_key_groups.extend([
            { "age": [ "YOUR-TEAM-MEMBER-AGE-KEY" ] },
            { "age": [ "BACKUP-AGE-KEYS" ] }
        ])

    rules = [
        {
            "path_regex": "(.*)?secrets/dev/.*\\.(ya?ml|json|env)",
            "shamir_threshold": 3,
            "key_groups": dev_key_groups
        },
        {
            "path_regex": "(.*)?secrets/prod/.*\\.(ya?ml|json|env)",
            "shamir_threshold": 4,
            "key_groups" : prod_key_groups
        }
    ]
    if person:
        rules.append({
            "path_regex": f".*ramblings/{person}/.*\\.(ya?ml|json|env)",
            "shamir_threshold": 3,
            "key_groups" : ramblings_key_groups
        })
    
    if not engine in ["age", "gpg", "both"]:
        console.print("Unsuported. Exiting.")
        sys.exit(1)

    sopsContent = {"creation_rules": rules}

    try:
        with open(sops_file, 'w') as f:
            yaml.dump(sopsContent, f, default_flow_style=False)

        console.print(f"[bold green]Success![/] SOPS configuration generated at: [dim]{sops_file}[/]")

    except Exception as e:
        console.print(f"[bold red]ERROR:[/] Failed to write config file: {e}")
        sys.exit(1)

    return engine

def _get_choices(hasAge: bool, hasPgp: bool) -> list[str]:
    choices = []
    if hasAge:
        choices.append('age')
    if hasPgp:
        choices.append('gpg')
    if hasPgp and hasAge:
        choices.append('both')
    return choices

def _validate_teamDir(path: str, company: str, team: str) -> Path:
    if not path:
        teamDir = Path(os.path.join(os.getcwd(), company, team))
    else:
        if '..' in path or path.startswith("/"):
            console.print(f"[bold red]ERROR:[/] Invalid path '{path}'.")
            sys.exit(1)

        if not Path(path).exists():
            console.print(f"[bold red]ERROR:[/] Specified path '{path}' does not exist.")
            sys.exit(1)

        teamDir = Path(os.path.join(path, company, team))
    return teamDir

def _list_teams_in_dir(baseDir: Path) -> set[str]:
    if not baseDir.is_dir():
        return set()
    teams = set([d.name for d in baseDir.iterdir() if d.is_dir() or d.is_symlink()])
    return teams

