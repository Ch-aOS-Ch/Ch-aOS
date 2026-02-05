from omegaconf import OmegaConf
from rich.console import Console
from rich.prompt import Confirm
from pathlib import Path
import subprocess
import shutil
from chaos.lib.teamUtils import (
    _validate_deps,
    _get_choices,
    _validate_paths,
    _validate_teamDir,
    _create_sops_config,
    _create_chaos_file,
    _symlink_teamDir,
    _get_chaos_file,
    _list_teams_in_dir
)
import os

from chaos.lib.utils import checkDep, render_list_as_table, validate_path
"""Lmao yeah, a ton of stuff is happening in teamUtils.py"""

console = Console()

"""
Module for managing team structures, including initialization, activation, deactivation, listing, cloning, and pruning.
"""

def initTeam(args):
    """
    Initializes a new team structure with the specified parameters.

    Check the corresponding functions in teamUtils.py for detailed implementations of each step.
    + the documentation there.
    """
    hasAge, hasPgp = _validate_deps()
    choices = _get_choices(hasAge, hasPgp)

    company, team, person = _validate_paths(args)

    path = args.path
    ikwid = args.i_know_what_im_doing

    confirm = True if ikwid else Confirm.ask(f"Initialize secrets structure for team [bold]{team}[/] at company [bold]{company}[/]" + (f", person [bold]{person}[/]" if person else "") + "?", default=True)
    if not confirm:
        console.print("[yellow]Operation cancelled by user.[/]")
        return

    teamDir = _validate_teamDir(path, company, team)

    gitDir = teamDir / ".git"
    if not gitDir.exists():
        confirm = True if ikwid else Confirm.ask(f"The directory {teamDir} is not a git repository. Initialize a new git repository here?", default=False)
        if confirm:
            subprocess.run(["git", "init", str(teamDir)], check=True)

    teamDir.mkdir(parents=True, exist_ok=True)

    rambleTeamDir = teamDir / f"ramblings/{person}" if person else teamDir / "ramblings"
    rambleTeamDir.mkdir(parents=True, exist_ok=True)

    secretsTeamDir = teamDir / "secrets"
    devSecs = secretsTeamDir / "dev"
    devSecs.mkdir(parents=True, exist_ok=True)
    prodSecs = secretsTeamDir / "prod"
    prodSecs.mkdir(parents=True, exist_ok=True)

    engine = _create_sops_config(teamDir, hasAge, choices, person, ikwid)
    if engine is None:
        return

    _create_chaos_file(path, company, team, person, engine)

    base_path = Path(path).resolve() if path else Path(os.getcwd()).resolve()
    _symlink_teamDir(company, base_path, team)

def activateTeam(args):
    """
    Activates a team by reading the .chaos.yml file and creating necessary symlinks.
    """
    path = args.path
    chaosContent = _get_chaos_file(path)
    company = chaosContent.get('company')
    team = chaosContent.get('team')
    engines = chaosContent.get('engine')

    if not company or not team:
        raise ValueError(".chaos.yml is missing 'company' or 'team' information.")

    if not engines:
        raise ValueError(".chaos.yml is missing 'engine' information.")

    for engine in engines:
        if engine not in ["age", "gpg"]:
            console.print(f"[bold yellow]WARNING:[/] Unsupported engine '{engine}' in .chaos.yml. Supported engines are 'age' and 'gpg'.")
            continue
        _validate_deps()
        if engine == "age":
            if not checkDep('age-keygen'):
                console.print("[bold red]CRITICAL:[/] age-keygen is not installed. It is required for age engine.")
                continue

        if engine == "gpg":
            if not checkDep('gpg'):
                console.print("[bold red]CRITICAL:[/] gpg is not installed. It is required for gpg engine.")
                continue

    _ = _validate_teamDir(args.path, company, team)
    base_path = Path(args.path).resolve() if args.path else Path(os.getcwd()).resolve()
    _symlink_teamDir(company, base_path, team)

def cloneGitTeam(args):
    """
    Clones a git repository and activates the team if valid.

    Validity = presence of .chaos.yml with required fields.
    """
    from git import Repo

    repo = args.target
    path = args.path
    clone_dir = path if path else repo.split('/')[-1].replace('.git', '')
    validate_path(clone_dir)

    try:
        if path:
            Repo.clone_from(repo, path)
        else:
            Repo.clone_from(repo, repo.split('/')[-1].replace('.git', ''))
    except subprocess.CalledProcessError as e:
        raise RuntimeError(f"Failed to clone repository '{repo}': {e}") from e

    chaos_file_path = Path(clone_dir) / ".chaos.yml"
    if not chaos_file_path.is_file():
        shutil.rmtree(clone_dir)
        raise FileNotFoundError(".chaos.yml not found in the cloned repository. Removed cloned directory.")

    chaosContent = _get_chaos_file(clone_dir)
    company = chaosContent.get('company')
    team = chaosContent.get('team')
    if not company or not team:
        shutil.rmtree(clone_dir)
        raise ValueError(".chaos.yml is missing 'company' or 'team' information. Removed cloned directory.")

    base_path = Path(clone_dir).resolve()
    _ = _validate_teamDir(clone_dir, company, team)
    _symlink_teamDir(company, base_path, team)

def listTeams(args):
    """Lists all activated teams, optionally filtered by company."""
    company = args.company
    baseDir = Path(f"~/.local/share/chaos/teams/{company}").expanduser() if company else Path("~/.local/share/chaos/teams").expanduser()
    if not baseDir.exists():
        console.print("[bold yellow]No teams have been activated yet.[/]")
        return
    teams = _list_teams_in_dir(baseDir)
    if not teams:
        console.print("[bold yellow]No teams have been activated yet.[/]")
        return

    if args.no_pretty:
        if args.json:
            import json as js
            print(js.dumps(OmegaConf.to_container(OmegaConf.create(list(teams))), indent=2))
            return
        print(OmegaConf.to_yaml(OmegaConf.create(list(teams))))
        return
    title = "[italic][green]Found teams:[/][/]"
    render_list_as_table(list(teams), title)

def deactivateTeam(args):
    """Deactivates specified teams or all teams for a company."""
    company = args.company
    if not company:
        raise ValueError("Company name is required to deactivate.")

    company_dir = Path.home() / ".local" / "share" / "chaos" / "teams" / company
    if not company_dir.is_dir():
        console.print(f"[bold yellow]Warning:[/] Company '{company}' has no active teams.")
        return

    teams_to_deactivate = args.teams

    if not teams_to_deactivate:
        if not Confirm.ask(f"[bold]Deactivate all teams for company '{company}'?[/]", default=False):
            console.print("[yellow]Operation cancelled.[/]")
            return

        active_teams = [p for p in company_dir.iterdir() if p.is_symlink()]
        if not active_teams:
            console.print(f"No active teams found for company '{company}'.")
            try:
                company_dir.rmdir()
                console.print(f"Removed empty directory for company '{company}'.")
            except OSError:
                pass # Directory might not be empty, fail silently.
            return

        for team_link in active_teams:
            team_link.unlink()

        console.print(f"[bold green]Success![/] All teams for company '{company}' deactivated.")
        try:
            company_dir.rmdir()
        except OSError:
            pass
        return

    for team_name in teams_to_deactivate:
        if '/' in team_name or '..' in team_name:
            console.print(f"[bold yellow]WARNING:[/] Skipping invalid team name '{team_name}'.")
            continue

        team_link = company_dir / team_name
        if team_link.is_symlink():
            team_link.unlink()
            console.print(f"Team '{team_name}' deactivated.")
        else:
            console.print(f"[bold yellow]Warning:[/] Team '{team_name}' is not an active symlink. Skipping.")

    try:
        if not any(company_dir.iterdir()):
            company_dir.rmdir()
    except OSError:
        pass

def pruneTeams(args):
    """Prunes stale team symlinks that point to non-existent directories."""
    confirm = True if args.i_know_what_im_doing else Confirm.ask("Prune stale team symlinks? This may take some time.", default=False)
    if not confirm:
        console.print("[yellow]Operation cancelled by user.[/]")
        return

    companies = args.companies
    baseDir = Path.home() / ".local" / "share" / "chaos" / "teams"
    if not baseDir.is_dir():
        console.print("[bold yellow]No teams have been activated yet.[/]")
        return
    pruned_count = 0
    if not companies:
        company_names = [d.name for d in baseDir.iterdir() if d.is_dir()]
    else:
        company_names = companies

    for company_name in company_names:
        company_dir = baseDir / company_name
        for team_entry in list(company_dir.iterdir()):
            if not team_entry.is_symlink():
                console.print(f"Skipping non-symlink entry: {team_entry}")
                continue

            if not team_entry.resolve().exists():
                console.print(f"Pruning stale team symlink: {team_entry}")
                team_entry.unlink()
                pruned_count += 1

        try:
            if not any(company_dir.iterdir()):
                company_dir.rmdir()
                console.print(f"Removed empty company directory: {company_dir}")
        except OSError:
            pass

    if pruned_count == 0:
        console.print("[bold green]No stale team symlinks found to prune.[/]")
    else:
        console.print(f"[bold green]Pruned {pruned_count} stale team symlink(s).[/]")
