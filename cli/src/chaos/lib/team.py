"""Module for managing team structures, including initialization, activation, deactivation, listing, cloning, and pruning."""

import os
import shutil
import subprocess
from pathlib import Path

from chaos.lib.args.dataclasses import (
    DataGatherPayload,
    DataGatherRequest,
    ResultPayload,
    TeamActivatePayload,
    TeamClonePayload,
    TeamDeactivatePayload,
    TeamInitPayload,
    TeamListPayload,
    TeamPrunePayload,
)
from chaos.lib.teamUtils import (
    _create_chaos_file,
    _create_sops_config,
    _get_chaos_file,
    _get_choices,
    _list_teams_in_dir,
    _symlink_teamDir,
    _validate_deps,
    _validate_paths,
    _validate_teamDir,
)
from chaos.lib.utils import checkDep, validate_path


def gatherInitTeam(payload: TeamInitPayload) -> DataGatherRequest | None:
    """Gathers data needed to initialize a team structure.

    Args:
        payload (TeamInitPayload): The initial payload detailing the team configuration and requirements.

    Returns:
        DataGatherRequest | None: A request containing prompts to clarify options from the user, or None if no extra inputs are needed.
    """
    try:
        hasAge, hasPgp = _validate_deps()
    except EnvironmentError:
        return None

    choices = _get_choices(hasAge, hasPgp)
    try:
        company, team, person = _validate_paths(payload.target)
    except ValueError:
        return None

    path = payload.path
    if not path:
        path = os.getcwd()

    ikwid = payload.i_know_what_im_doing

    if ikwid:
        return None

    fields = []

    fields.append(
        DataGatherPayload(
            name="confirmed",
            prompt=f"Initialize secrets structure for team {team} at company [bold]{company}"
            + (f", person {person}" if person else "")
            + "?",
            input_type="boolean",
            required=True,
            default=True,
        )
    )

    gitDir = Path(path) / ".git"
    if not gitDir.exists():
        fields.append(
            DataGatherPayload(
                name="init_git",
                prompt=f"The directory {path} is not a git repository. Initialize a new git repository here?",
                input_type="boolean",
                required=True,
                default=False,
            )
        )

    try:
        teamDir = _validate_teamDir(path, company, team)
    except FileNotFoundError:
        teamDir = Path(os.path.join(path, company, team))

    sops_file = teamDir / "sops-config.yml"
    if sops_file.exists():
        fields.append(
            DataGatherPayload(
                name="overwrite_sops",
                prompt=f"A sops configuration already exists at {sops_file}. Overwrite?",
                input_type="boolean",
                required=True,
                default=False,
            )
        )

    default_engine = "age" if hasAge else "gpg"
    fields.append(
        DataGatherPayload(
            name="engine",
            prompt="Choose encryption engine",
            input_type="choice",
            choices=choices,
            required=True,
            default=default_engine,
        )
    )

    hasVault = checkDep("vault")
    if hasVault:
        fields.append(
            DataGatherPayload(
                name="use_vault",
                prompt="Do you wish to use vault? (recommended for security)",
                input_type="boolean",
                required=True,
                default=True,
            )
        )
    else:
        fields.append(
            DataGatherPayload(
                name="continue_no_vault",
                prompt="Vault is not installed. Do you wish to continue without vault?",
                input_type="boolean",
                required=True,
                default=False,
            )
        )

    if fields:
        return DataGatherRequest(name="team_init", fields=fields)
    return None


def handleInitTeam(payload: TeamInitPayload) -> ResultPayload[None]:
    """Handles the initialization of the directory structure and required configurations for a team.

    Args:
        payload (TeamInitPayload): The fully resolved payload (post-gathering) necessary for setup.

    Returns:
        ResultPayload[None]: Status payload indicating the result and reporting any issues.
    """
    messages = []

    try:
        hasAge, hasPgp = _validate_deps()
        choices = _get_choices(hasAge, hasPgp)
        company, team, person = _validate_paths(payload.target)
    except (EnvironmentError, ValueError) as e:
        return ResultPayload(success=False, error=[str(e)])

    path = payload.path
    if not path:
        path = os.getcwd()

    ikwid = payload.i_know_what_im_doing

    confirm = payload.confirmed if not ikwid else True
    if not confirm:
        return ResultPayload(success=False, error=["Operation cancelled by user."])

    try:
        teamDir = _validate_teamDir(path, company, team)
    except FileNotFoundError as e:
        return ResultPayload(success=False, error=[str(e)])

    gitDir = Path(path) / ".git"
    if not gitDir.exists():
        init_git = payload.init_git if not ikwid else True
        if init_git:
            try:
                subprocess.run(
                    ["git", "init", str(path)], check=True, capture_output=True
                )
                messages.append("Initialized a new git repository.")
            except subprocess.CalledProcessError as e:
                return ResultPayload(
                    success=False, error=[f"Failed to initialize git repository: {e}"]
                )

    teamDir.mkdir(parents=True, exist_ok=True)

    rambleTeamDir = teamDir / f"ramblings/{person}" if person else teamDir / "ramblings"
    rambleTeamDir.mkdir(parents=True, exist_ok=True)

    secretsTeamDir = teamDir / "secrets"
    devSecs = secretsTeamDir / "dev"

    devSecs.mkdir(parents=True, exist_ok=True)
    prodSecs = secretsTeamDir / "prod"

    prodSecs.mkdir(parents=True, exist_ok=True)

    sops_file = teamDir / "sops-config.yml"
    if sops_file.exists():
        overwrite = payload.overwrite_sops if not ikwid else True
        if not overwrite:
            messages.append("Operation cancelled. Keeping existing config.")
            return ResultPayload(
                success=False, error=["Operation cancelled. Keeping existing config."]
            )

    engine_choice = payload.engine if not ikwid else ("age" if hasAge else "gpg")
    if not engine_choice:
        engine_choice = "age" if hasAge else "gpg"

    hasVault = checkDep("vault")

    useVault = (
        payload.use_vault
        if hasVault and not ikwid
        else (True if hasVault and ikwid else False)
    )

    if not hasVault:
        cont = payload.continue_no_vault if not ikwid else True
        if not cont:
            return ResultPayload(
                success=False,
                error=["Operation cancelled. Please install vault and try again."],
            )

    try:
        engine = _create_sops_config(
            teamDir, hasAge, choices, person, ikwid, engine_choice, useVault
        )
    except Exception as e:
        return ResultPayload(success=False, error=[str(e)])

    if engine is None:
        return ResultPayload(success=False, error=["Failed to create sops config."])

    try:
        _create_chaos_file(path, company, team, person, engine)
        base_path = Path(path).resolve() if path else Path(os.getcwd()).resolve()
        msg = _symlink_teamDir(company, base_path, team)
        messages.append(msg)
    except Exception as e:
        return ResultPayload(success=False, error=[str(e)])

    return ResultPayload(success=True, message=messages)


def handleActivateTeam(payload: TeamActivatePayload) -> ResultPayload[None]:
    """Activates a team by reading the .chaos.yml file and creating necessary symlinks.

    Args:
        payload (TeamActivatePayload): Payload containing the target path context to read the configuration from.

    Returns:
        ResultPayload[None]: Status representation of symlink deployments and setup validations.
    """
    messages = []
    errors = []

    path = payload.path
    try:
        chaosContent = _get_chaos_file(path)
    except Exception as e:
        return ResultPayload(success=False, error=[str(e)])

    company = chaosContent.get("company", "")
    teams = chaosContent.get("teams", [])
    engines = chaosContent.get("engine", [])

    if not company or not teams:
        return ResultPayload(
            success=False,
            error=[".chaos.yml is missing 'company' or 'team' information."],
        )

    if not engines:
        return ResultPayload(
            success=False, error=[".chaos.yml is missing 'engine' information."]
        )

    for engine in engines:
        if engine not in ["age", "gpg"]:
            errors.append(
                f"Unsupported engine '{engine}' in .chaos.yml. Supported engines are 'age' and 'gpg'."
            )
            continue
        try:
            _validate_deps()
        except EnvironmentError as e:
            errors.append(str(e))
            continue

        if engine == "age":
            if not checkDep("age-keygen"):
                errors.append(
                    "age-keygen is not installed. It is required for age engine."
                )
                continue

        if engine == "gpg":
            if not checkDep("gpg"):
                errors.append("gpg is not installed. It is required for gpg engine.")
                continue

    if errors and not any(
        e
        for e in engines
        if e in ["age", "gpg"] and checkDep(e) or checkDep(f"{e}-keygen")
    ):
        return ResultPayload(success=False, error=errors)

    path = payload.path
    if not path:
        path = os.getcwd()

    for team in teams:
        try:
            _ = _validate_teamDir(path, company, team.get("name", ""))
            base_path = (
                Path(path).resolve() if payload.path else Path(os.getcwd()).resolve()
            )
            msg = _symlink_teamDir(company, base_path, team.get("name", ""))
            messages.append(msg)
        except Exception as e:
            errors.append(str(e))

    if errors:
        return ResultPayload(success=False, message=messages, error=errors)

    return ResultPayload(success=True, message=messages)


def handleCloneGitTeam(payload: TeamClonePayload) -> ResultPayload[None]:
    """Clones a git repository and activates the team if valid.

    Args:
        payload (TeamClonePayload): Payload supplying git repository details and target local path.

    Returns:
        ResultPayload[None]: Results containing operations metadata or rollback trace logs on failure.

    Notes:
        Validity relies on the presence of a properly configured `.chaos.yml`.
    """
    repo = payload.target
    path = payload.path
    clone_dir = path if path else repo.split("/")[-1].replace(".git", "")
    try:
        validate_path(clone_dir)
    except ValueError as e:
        return ResultPayload(success=False, error=[str(e)])

    try:
        if path:
            subprocess.run(
                ["git", "clone", repo, path], check=True, capture_output=True
            )
        else:
            subprocess.run(["git", "clone", repo], check=True, capture_output=True)
    except subprocess.CalledProcessError as e:
        return ResultPayload(
            success=False, error=[f"Failed to clone repository '{repo}': {e}"]
        )

    chaos_file_path = Path(clone_dir) / ".chaos.yml"
    if not chaos_file_path.is_file():
        shutil.rmtree(clone_dir)
        return ResultPayload(
            success=False,
            error=[
                ".chaos.yml not found in the cloned repository. Removed cloned directory."
            ],
        )

    try:
        chaosContent = _get_chaos_file(clone_dir)
    except Exception as e:
        shutil.rmtree(clone_dir)
        return ResultPayload(success=False, error=[str(e)])

    company = chaosContent.get("company")
    teams = chaosContent.get("teams")
    if not company or not teams:
        shutil.rmtree(clone_dir)
        return ResultPayload(
            success=False,
            error=[
                ".chaos.yml is missing 'company' or 'team' information. Removed cloned directory."
            ],
        )

    messages = []
    errors = []
    for team in teams:
        base_path = Path(clone_dir).resolve()
        try:
            _ = _validate_teamDir(clone_dir, company, team.get("name", ""))
            msg = _symlink_teamDir(company, base_path, team.get("name", ""))
            messages.append(msg)
        except Exception as e:
            errors.append(str(e))

    if errors:
        return ResultPayload(success=False, message=messages, error=errors)

    return ResultPayload(success=True, message=messages)


def listTeams(payload: TeamListPayload) -> ResultPayload[dict[str, list[str]]]:
    """Lists all activated teams, optionally filtered by company.

    Args:
        payload (TeamListPayload): Constraints mapping the query filters (e.g. company name).

    Returns:
        ResultPayload[dict[str, list[str]]]: Found directories matching specified target query.
    """
    messages = []

    result = ResultPayload(message=messages, success=True, data=None, error=None)

    company = payload.company

    baseDir = (
        Path(
            os.getenv(
                "CHAOS_TEAMS_DIR",
                Path.home() / ".local" / "share" / "chaos" / "teams",
            )
        ).expanduser()
        / company
        if company
        else Path(
            os.getenv(
                "CHAOS_TEAMS_DIR", Path.home() / ".local" / "share" / "chaos" / "teams"
            )
        ).expanduser()
    )

    if not baseDir.exists():
        messages.append("No teams have been activated yet.")
        result.success = False
        return result

    teams = _list_teams_in_dir(baseDir)

    if not teams:
        messages.append("No teams have been activated yet.")
        result.success = False
        return result

    result.data = teams
    return result


def gatherDeactivateTeam(payload: TeamDeactivatePayload) -> DataGatherRequest | None:
    """Gathers confirmation for a comprehensive deactivation.

    Args:
        payload (TeamDeactivatePayload): Instructions targeting a specific company setup to sever.

    Returns:
        DataGatherRequest | None: User confirmation request if required, or None.
    """
    company = payload.company
    if not company:
        return None

    teams_to_deactivate = payload.teams
    if not teams_to_deactivate:
        return DataGatherRequest(
            name="team_deactivate",
            fields=[
                DataGatherPayload(
                    name="confirmed",
                    prompt=f"Deactivate all teams for company '{company}'?",
                    input_type="boolean",
                    required=True,
                    default=False,
                )
            ],
        )
    return None


def handleDeactivateTeam(payload: TeamDeactivatePayload) -> ResultPayload[None]:
    """Deactivates specified teams or all teams for a company.

    Args:
        payload (TeamDeactivatePayload): Details specifying the subset of teams to purge or if a complete teardown is targeted.

    Returns:
        ResultPayload[None]: Feedback referencing all unlinked setups.
    """
    company = payload.company
    if not company:
        return ResultPayload(
            success=False, error=["Company name is required to deactivate."]
        )

    company_dir = Path.home() / ".local" / "share" / "chaos" / "teams" / company
    if not company_dir.is_dir():
        return ResultPayload(
            success=False, error=[f"Company '{company}' has no active teams."]
        )

    teams_to_deactivate = payload.teams
    messages = []
    errors = []

    if not teams_to_deactivate:
        if not payload.confirmed:
            return ResultPayload(success=False, error=["Operation cancelled."])

        active_teams = [p for p in company_dir.iterdir() if p.is_symlink()]
        if not active_teams:
            try:
                company_dir.rmdir()
                messages.append(f"Removed empty directory for company '{company}'.")
            except OSError:
                pass  # Directory might not be empty, fail silently.
            return ResultPayload(success=True, message=messages)

        for team_link in active_teams:
            team_link.unlink()

        messages.append(f"All teams for company '{company}' deactivated.")
        try:
            company_dir.rmdir()
        except OSError:
            pass
        return ResultPayload(success=True, message=messages)

    for team_name in teams_to_deactivate:
        if "/" in team_name or ".." in team_name:
            errors.append(f"Skipping invalid team name '{team_name}'.")
            continue

        team_link = company_dir / team_name
        if team_link.is_symlink():
            team_link.unlink()
            messages.append(f"Team '{team_name}' deactivated.")
        else:
            errors.append(f"Team '{team_name}' is not an active symlink. Skipping.")

    try:
        if not any(company_dir.iterdir()):
            company_dir.rmdir()
    except OSError:
        pass

    return ResultPayload(success=True, message=messages, error=errors)


def gatherPruneTeams(payload: TeamPrunePayload) -> DataGatherRequest | None:
    """Prompts the user before pruning stale records.

    Args:
        payload (TeamPrunePayload): Context wrapping parameters and `i_know_what_im_doing` flag.

    Returns:
        DataGatherRequest | None: Confirmation requirement prompt, if lacking the automated override flag.
    """
    if payload.i_know_what_im_doing:
        return None

    return DataGatherRequest(
        name="team_prune",
        fields=[
            DataGatherPayload(
                name="confirmed",
                prompt="Prune stale team symlinks? This may take some time.",
                input_type="boolean",
                required=True,
                default=False,
            )
        ],
    )


def handlePruneTeams(payload: TeamPrunePayload) -> ResultPayload[None]:
    """Prunes stale team symlinks that point to non-existent directories.

    Args:
        payload (TeamPrunePayload): Defines the scope (all companies or specific targets) to run the pruning script against.

    Returns:
        ResultPayload[None]: Metrics encapsulating the total number of pruned paths.
    """
    confirm = payload.confirmed if not payload.i_know_what_im_doing else True
    if not confirm:
        return ResultPayload(success=False, error=["Operation cancelled by user."])

    companies = payload.companies
    baseDir = Path.home() / ".local" / "share" / "chaos" / "teams"
    if not baseDir.is_dir():
        return ResultPayload(success=False, error=["No teams have been activated yet."])

    pruned_count = 0
    messages = []

    if not companies:
        company_names = [d.name for d in baseDir.iterdir() if d.is_dir()]
    else:
        company_names = companies

    for company_name in company_names:
        company_dir = baseDir / company_name
        if not company_dir.exists():
            continue

        for team_entry in list(company_dir.iterdir()):
            if not team_entry.is_symlink():
                messages.append(f"Skipping non-symlink entry: {team_entry}")
                continue

            if not team_entry.resolve().exists():
                messages.append(f"Pruning stale team symlink: {team_entry}")
                team_entry.unlink()
                pruned_count += 1

        try:
            if not any(company_dir.iterdir()):
                company_dir.rmdir()
                messages.append(f"Removed empty company directory: {company_dir}")
        except OSError:
            pass

    if pruned_count == 0:
        messages.append("No stale team symlinks found to prune.")
    else:
        messages.append(f"Pruned {pruned_count} stale team symlink(s).")

    return ResultPayload(success=True, message=messages)

