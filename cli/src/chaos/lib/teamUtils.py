import os
from pathlib import Path
from typing import Optional, cast

import yaml
from omegaconf import DictConfig, OmegaConf
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Confirm, Prompt

from chaos.lib.utils import checkDep

from .utils import validate_path

console = Console()

"""Team Utilities for Chaos CLI."""


def _validate_deps():
    """
    Checks the existence of some dependencies, be them required or optional.

    If adding a new dependency, make sure to make it clear whether it's required or optional.
    The ONLY required dependency should be sops, if you need to add more, something might be wrong.
    """
    hasAge = checkDep("age-keygen")
    hasSops = checkDep("sops")
    hasPgp = checkDep("gpg")

    if not hasSops:
        raise EnvironmentError(
            "sops is not installed. It is required for this software."
        )

    if not (hasAge or hasPgp):
        raise EnvironmentError(
            "Neither gpg nor age are installed. At least one is required for this functionality."
        )

    return hasAge, hasPgp


def _symlink_teamDir(company: str, base_path: Path, team: str):
    """
    Creates a symlink from the team directory to the chaos teams activation directory.

    If the symlink already exists and points to the same location, it does nothing.
    If it points to a different location, it raises an error.
    If a file or directory already exists at the activation path, it raises an error.

    If neither of those, it creates the symlink and notifies the user.
    """
    try:
        src = base_path / f"{company}/{team}"
        dest = Path(f"~/.local/share/chaos/teams/{company}/{team}").expanduser()

        dest.parent.mkdir(parents=True, exist_ok=True)

        if dest.is_symlink():
            if dest.resolve() == src.resolve():
                console.print(
                    f"[bold green]Success![/] Team [bold]{team}[/] from company [bold]{company}[/] is already active."
                )
                return
            else:
                raise FileExistsError(
                    f"Another project for team '{team}' in company '{company}' is already active from a different path."
                )
        elif dest.exists():
            raise FileExistsError(
                f"A file or directory already exists at the activation path: {dest}"
            )

        dest.symlink_to(src, target_is_directory=True)

        console.print(
            f"[bold green]Success![/] Team [bold]{team}[/] from company [bold]{company}[/] activated at [dim]{dest}[/]"
        )
    except Exception as e:
        raise RuntimeError(f"Failed to activate team: {e}") from e


def _validate_paths(batch: str):
    """Protection against path traversal and invalid names."""

    parts = batch.split(".")
    company = parts[0]
    team = parts[1]
    person = parts[2] if len(parts) == 3 else None

    if "." not in batch:
        raise ValueError("Must set a company for your team. (company.team.person)")
    if not team or not company:
        raise ValueError("Must pass both team and company.")

    if person:
        if ".." in person or person.startswith("/"):
            raise ValueError(f"Invalid group name '{person}'.")

    if ".." in company or company.startswith("/"):
        raise ValueError(f"Invalid company name '{company}'.")

    if ".." in team or team.startswith("/"):
        raise ValueError(f"Invalid team name '{team}'.")

    return company, team, person


def _create_chaos_file(path, company: str, team: str, person: str | None, engine: str):
    """
    Creates a .chaos.yml file in the specified path with the given parameters.
    """
    chaos_file = (
        Path(os.path.join(os.getcwd())) / ".chaos.yml"
        if not path
        else Path(path) / ".chaos.yml"
    )
    if not chaos_file.exists():
        chaosContent = {
            "company": company,
            "teams": [team],
            "people": [person] if person else [],
            "engine": [engine] if engine != "both" else ["age", "gpg"],
        }

        yaml.dump(chaosContent, open(chaos_file, "w"), default_flow_style=False)

    else:
        chaosContent = yaml.load(open(chaos_file, "r"), Loader=yaml.FullLoader)
        if team not in chaosContent.get("teams", []):
            chaosContent["teams"].append(team)

        if person and person not in chaosContent.get("people", []):
            chaosContent["people"].append(person)

        engines = chaosContent.get("engine", [])
        if engine == "both":
            if "age" not in engines:
                engines.append("age")

            if "gpg" not in engines:
                engines.append("gpg")

        elif engine not in engines:
            engines.append(engine)
            chaosContent["engine"] = engines

        yaml.dump(chaosContent, open(chaos_file, "w"), default_flow_style=False)


def _get_chaos_file(path) -> DictConfig:
    """
    Loads and validates the .chaos.yml file in the specified path.
    """
    chaos_file = (
        Path(os.path.join(os.getcwd())) / ".chaos.yml"
        if not path
        else Path(path) / ".chaos.yml"
    )
    if not chaos_file.exists():
        raise FileNotFoundError("No .chaos.yml file found in current directory.")

    chaosContent = OmegaConf.load(chaos_file)
    chaosContent = cast(DictConfig, chaosContent)
    if (
        not chaosContent.get("company")
        or not chaosContent.get("teams")
        or not chaosContent.get("engine")
    ):
        raise ValueError(
            ".chaos.yml file is missing required fields (company, team, engine)."
        )

    return chaosContent


def _create_sops_config(
    teamDir, hasAge: bool, choices: list[str], person: str | None, ikwid
) -> Optional[str]:
    """
    Creates a sops-config.yml file in the team directory with the appropriate configuration.

    The config follows the following structure:
    For RAMBLINGS:
    4kSSS: 4 keys with a shamir of 3, it has the team member's key (this group can have more keys, if the dev wants to share their ramblings) and the backup keys, as well as the team vault key and company vault key if vault is used.

    For DEV:
    4kSSS-U: 4 keys with a shamir of 3, it has the team's unified key and the backup keys, as well as the team vault key and company vault key if vault is used.

    For PROD:
    6kSSS: 6 keys with a shamir of 4, it has each team member's key inside one singular group and the backup keys, as well as the team vault key, company vault key, security team vault key and compliance team vault key if vault is used.

    Yeah Yeah, it's kinda big, but it's flexible, secure and more importantly: It does one singular thing.
    """
    sops_file = teamDir / "sops-config.yml"
    if sops_file.exists():
        if not Confirm.ask(
            f"A sops configuration already exists at [dim]{sops_file}[/]. Overwrite?",
            default=False,
        ):
            console.print("[yellow]Operation cancelled. Keeping existing config.[/]")
            return None

    default = "age" if hasAge else "gpg"
    console.print(
        Panel(
            "Chaos uses [bold]SOPS[/] for encryption.\nYou need to choose a backend engine to handle the keys.",
            title="Secrets Initialization",
            border_style="green",
        )
    )
    engine = (
        "age"
        if ikwid
        else Prompt.ask("Choose encryption engine", choices=choices, default=default)
    )

    dev_key_groups = []
    prod_key_groups = []
    ramblings_key_groups = []

    hasVault = checkDep("vault")

    if hasVault:
        useVault = (
            True
            if ikwid
            else Confirm.ask(
                "Do you wish to use vault? (recommended for security)", default=True
            )
        )
        if useVault:
            dev_key_groups.extend(
                [
                    {"hc_vault": ["VAULT-TEAM-URI-INSTANCE."]},
                    {"hc_vault": ["VAULT-COMPANY-URI-INSTANCE"]},
                ]
            )
            prod_key_groups.extend(
                [
                    {"hc_vault": ["VAULT-TEAM-URI-INSTANCE."]},
                    {"hc_vault": ["VAULT-COMPANY-URI-INSTANCE"]},
                    {"hc_vault": ["VAULT-SECURITY-TEAM-URI-INSTANCE"]},
                    {"hc_vault": ["VAULT-COMPLIANCE-TEAM-URI-INSTANCE"]},
                ]
            )
            ramblings_key_groups.extend(
                [
                    {"hc_vault": ["VAULT-TEAM-URI-INSTANCE."]},
                    {"hc_vault": ["VAULT-COMPANY-URI-INSTANCE"]},
                ]
            )
    else:
        console.print(
            "[bold yellow]WARNING:[/] Vault is not installed. Using vault is the more secure way to manage your secrets."
        )
        confirm = Confirm.ask("Do you wish to continue without vault?", default=False)
        if not confirm:
            raise RuntimeError(
                "Operation cancelled. Please install vault and try again."
            )

    if engine in ["gpg", "both"]:
        dev_key_groups.extend(
            [{"pgp": ["YOUR-TEAM-UNIFIED-PGP-KEYS"]}, {"pgp": ["BACKUP-PGP-KEYS"]}]
        )
        prod_key_groups.extend(
            [
                {"pgp": ["EACH-OF-YOUR-TEAM-MEMBERS-PGP-KEYS"]},
                {"pgp": ["BACKUP-PGP-KEYS"]},
            ]
        )
        ramblings_key_groups.extend(
            [{"pgp": ["YOUR-TEAM-MEMBER-PGP-KEY"]}, {"pgp": ["BACKUP-PGP-KEYS"]}]
        )

    if engine in ["age", "both"]:
        dev_key_groups.extend(
            [{"age": ["YOUR-TEAM-UNIFIED-AGE-KEYS"]}, {"age": ["BACKUP-AGE-KEYS"]}]
        )
        prod_key_groups.extend(
            [
                {"age": ["EACH-OF-YOUR-TEAM-MEMBERS-AGE-KEYS"]},
                {"age": ["BACKUP-AGE-KEYS"]},
            ]
        )
        ramblings_key_groups.extend(
            [{"age": ["YOUR-TEAM-MEMBER-AGE-KEY"]}, {"age": ["BACKUP-AGE-KEYS"]}]
        )

    rules = [
        {
            "path_regex": "(.*)?secrets/dev/.*\\.(ya?ml|json|env)",
            "shamir_threshold": 3,
            "key_groups": dev_key_groups,
        },
        {
            "path_regex": "(.*)?secrets/prod/.*\\.(ya?ml|json|env)",
            "shamir_threshold": 4,
            "key_groups": prod_key_groups,
        },
    ]
    if person:
        rules.append(
            {
                "path_regex": f".*ramblings/{person}/.*\\.(ya?ml|json|env)",
                "shamir_threshold": 3,
                "key_groups": ramblings_key_groups,
            }
        )

    if engine not in ["age", "gpg", "both"]:
        raise ValueError(f"Unsupported engine: {engine}")

    sopsContent = {"creation_rules": rules}

    try:
        with open(sops_file, "w") as f:
            yaml.dump(sopsContent, f, default_flow_style=False)

        console.print(
            f"[bold green]Success![/] SOPS configuration generated at: [dim]{sops_file}[/]"
        )

    except Exception as e:
        raise RuntimeError(f"Failed to write config file: {e}") from e

    return engine


def _get_choices(hasAge: bool, hasPgp: bool) -> list[str]:
    """Generates the list of choices for encryption engines based on available dependencies."""
    choices = []
    if hasAge:
        choices.append("age")
    if hasPgp:
        choices.append("gpg")
    if hasPgp and hasAge:
        choices.append("both")
    return choices


def _validate_teamDir(path: str, company: str, team: str) -> Path:
    """Validates and constructs the team directory path."""
    if not path:
        teamDir = Path(os.path.join(os.getcwd(), company, team))
    else:
        validate_path(path)

        if not Path(path).exists():
            raise FileNotFoundError(f"Specified path '{path}' does not exist.")

        teamDir = Path(os.path.join(path, company, team))
    return teamDir


def _list_teams_in_dir(baseDir: Path) -> set[str]:
    """Lists all teams in the specified base directory."""
    if not baseDir.is_dir():
        return set()
    teams = set([d.name for d in baseDir.iterdir() if d.is_dir() or d.is_symlink()])
    return teams
