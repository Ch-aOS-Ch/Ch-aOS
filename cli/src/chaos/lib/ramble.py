"""Module for managing ramble journals and pages.

Yeah, it's like a personal wiki or knowledge base, weird for a DevOps tool right? LMAO
Amazing for keeping track of random knowledge, scripts, concepts, and ideas related to chaos engineering and system administration.
Also, great for documenting secrets management strategies, configurations, and best practices.
"""

import os
import re
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import Any, cast

from chaos.lib.args.dataclasses import (
    DataGatherPayload,
    DataGatherRequest,
    RambleCreatePayload,
    RambleDeletePayload,
    RambleEditPayload,
    RambleEncryptPayload,
    RambleFindPayload,
    RambleMovePayload,
    RambleReadPayload,
    RambleUpdateEncryptPayload,
    ResultPayload,
    SecretsContext,
)
from chaos.lib.secret_backends.crypto import check_vault_auth, is_vault_in_use
from chaos.lib.secret_backends.utils import (
    _getProvider,
    _handle_provider_arg,
    decrypt_secrets,
)


def _get_ramble_dir(team) -> Path:
    """Validates and returns the ramble directory with the support for teams.

    Args:
        team (str | None): The team string formatted as 'company.team.person', or None for personal context.

    Returns:
        Path: The resolved directory path to the requested ramble context.

    Raises:
        ValueError: If the team string is formatted incorrectly or contains path traversal payloads.
        FileNotFoundError: If the team directory cannot be found.
    """
    if team:
        if "." not in team:
            raise ValueError("Must set a company for your team. (company.team.person)")

        parts = team.split(".")
        if len(parts) != 3:
            raise ValueError("Must set a person for your team. (company.team.person)")

        company, team, person = parts

        if ".." in person or person.startswith("/"):
            raise ValueError(f"Invalid person name '{person}'.")

        if ".." in company or company.startswith("/"):
            raise ValueError(f"Invalid company name '{company}'.")

        if ".." in team or team.startswith("/"):
            raise ValueError(f"Invalid team name '{team}'.")

        team_ramble_path = Path(
            os.getenv(
                "CHAOS_RAMBLE_DIR",
                Path.home() / ".local" / "share" / "chaos" / "teams" / company / team,
            )
        )

        if not team_ramble_path.exists():
            raise FileNotFoundError(
                f"Team ramble directory for '{team}' not found at {team_ramble_path}."
            )
        team_ramble_path = team_ramble_path / "ramblings" / person
        return team_ramble_path
    return Path(
        os.getenv(
            "CHAOS_RAMBLE_DIR", Path.home() / ".local" / "share" / "chaos" / "ramble"
        )
    )


def is_safe_path(target_path: Path, team) -> bool:
    """Validates that the target path is within the ramble directory to prevent path traversal.

    Args:
        target_path (Path): The path that is being accessed.
        team (str | None): The current team context.

    Returns:
        bool: True if the path is secure and valid.

    Raises:
        PermissionError: If path traversal is detected.
        FileNotFoundError: If the underlying ramble directory doesn't exist.
        ValueError: On generic path issues.
        RuntimeError: For other unexpected failures.
    """
    try:
        base_dir = _get_ramble_dir(team).resolve(strict=False)
        resolved_target = target_path.resolve(strict=False)

        if not resolved_target.is_relative_to(base_dir):
            raise PermissionError("Path traversal detected. Aborting.")
        return True
    except FileNotFoundError as e:
        raise FileNotFoundError("Ramble directory not found.") from e
    except ValueError as e:
        raise ValueError(f"Invalid path: {e}") from e
    except Exception as e:
        raise RuntimeError(f"Secure validation failed: {e}") from e


def _read_ramble_content(ramble_path, sops_config, context, global_config):
    """Reads the content of a ramble file, handling decryption if necessary.

    Args:
        ramble_path (Path): The path to the ramble page file.
        sops_config (str | None): The sops file configuration path.
        context (SecretsContext): The secrets context detailing override configs.
        global_config (dict | DictConfig): The global chaos configuration.

    Returns:
        tuple[DictConfig, str]: A tuple containing the parsed configuration and the raw text representation.

    Raises:
        FileNotFoundError: If the ramble page or `sops` binary is missing.
        ValueError: If the ramble is encrypted but no sops configuration was provided.
        PermissionError: If vault authentication fails.
        RuntimeError: If decryption fails or parsing issues occur.
    """
    is_safe_path(ramble_path, context.team)

    if not ramble_path.exists():
        raise FileNotFoundError(f"Ramble page not found: {ramble_path}")

    try:
        from omegaconf import OmegaConf

        data = OmegaConf.load(ramble_path)
        is_encrypted = "sops" in data

        if is_encrypted:
            if not sops_config:
                raise ValueError(
                    "This ramble appears to be encrypted, but no sops configuration was found.\n"
                    "   Provide one with '-ss /path/to/.sops.yml' or set a default with 'chaos set sops /path/to/.sops.yml'."
                )

            if is_vault_in_use(sops_config):
                is_authed, message = check_vault_auth()
                if not is_authed:
                    raise PermissionError(message)

            decrypted_text = None

            new_context = SecretsContext(
                team=context.team,
                sops_file_override=context.sops_file_override,
                secrets_file_override=str(ramble_path),
                provider_config=context.provider_config,
                i_know_what_im_doing=context.i_know_what_im_doing,
            )

            decrypted_text = decrypt_secrets(
                str(ramble_path), sops_config, global_config, new_context
            )

            ramble_data = OmegaConf.create(decrypted_text)
            return ramble_data, decrypted_text
        else:
            ramble_data = data
            with open(ramble_path, "r") as f:
                text = f.read()
            return ramble_data, text

    except subprocess.CalledProcessError as e:
        raise RuntimeError(f"Ramble decryption with sops failed.\n{e.stderr}") from e
    except FileNotFoundError as e:
        raise FileNotFoundError(
            "File not found or `sops` command not found. Please check the path and that sops is installed."
        ) from e
    except Exception as e:
        raise RuntimeError(
            f"Could not read or parse ramble file: {ramble_path}: {e}"
        ) from e


def gatherReadRamble(payload: RambleReadPayload) -> DataGatherRequest | None:
    """Analyzes the read targets and returns a DataGatherRequest if any journals need page selection.

    Args:
        payload (RambleReadPayload): Payload specifying the reading target context.

    Returns:
        DataGatherRequest | None: The user prompt to select a page, if applicable.
    """
    fields = []
    try:
        CONFIG_DIR = _get_ramble_dir(payload.context.team)
    except (ValueError, FileNotFoundError):
        return None

    for target in payload.targets:
        if ".." in target or "/" in target:
            continue

        parts = target.split(".", 1)
        journal = parts[0]
        is_list_request = (len(parts) > 1 and parts[1] == "list") or len(parts) == 1

        if not is_list_request:
            continue

        path = CONFIG_DIR / journal

        if not path.exists() and path.is_dir():
            continue

        entries = sorted([f.name for f in path.iterdir() if f.is_file()])

        if entries:
            choices = [Path(e).stem for e in entries]
            fields.append(
                DataGatherPayload(
                    name=f"read_{target}",
                    prompt=f"Which page do you want to read in journal '{journal}'?",
                    input_type="choice",
                    choices=choices,
                    required=True,
                )
            )

    if fields:
        return DataGatherRequest(name="ramble_read", fields=fields)
    return None


def gatherCreateRamble(payload: RambleCreatePayload) -> DataGatherRequest | None:
    """Checks if the ramble already exists and asks for confirmation to edit.

    Args:
        payload (RambleCreatePayload): The context and target payload for creating the ramble.

    Returns:
        DataGatherRequest | None: A request for user confirmation if the page already exists, otherwise None.
    """
    ramble = payload.target
    if ".." in ramble or "/" in ramble:
        return None
    team = payload.context.team

    try:
        CONFIG_DIR = _get_ramble_dir(team)
    except (ValueError, FileNotFoundError):
        return None

    if "." in ramble:
        parts = ramble.split(".", 1)
        directory = parts[0]
        page = parts[1]
        path = CONFIG_DIR / directory
        CONFIG_FILE_PATH = path / f"{page}.yml"
    else:
        path = CONFIG_DIR / ramble
        CONFIG_FILE_PATH = path / f"{ramble}.yml"

    if CONFIG_FILE_PATH.exists():
        return DataGatherRequest(
            name="ramble_create_confirm",
            fields=[
                DataGatherPayload(
                    name="confirmed",
                    prompt=f"Page {ramble} already exists! Do you want to go write on it?",
                    input_type="boolean",
                    required=True,
                    default=False,
                )
            ],
        )
    return None


def handleCreateRamble(payload: RambleCreatePayload) -> ResultPayload[dict[str, Any]]:
    """Creates a new ramble journal or page, and returns the file path to open.

    Args:
        payload (RambleCreatePayload): The creation instructions including the target and confirmation status.

    Returns:
        ResultPayload[dict[str, Any]]: A payload containing the created file path or editing instructions on success.
    """
    ramble = payload.target
    team = payload.context.team
    try:
        CONFIG_DIR = _get_ramble_dir(team)
    except (ValueError, FileNotFoundError) as e:
        return ResultPayload(success=False, error=[str(e)])

    should_encrypt = payload.encrypt

    if "." in ramble:
        parts = ramble.split(".", 1)
        directory = parts[0]
        page = parts[1]
        if not page or ".." in directory or "/" in directory:
            return ResultPayload(
                success=False, error=["Invalid format for journal.page"]
            )
        path = CONFIG_DIR / directory
        CONFIG_FILE_PATH = path / f"{page}.yml"
    else:
        if ".." in ramble or "/" in ramble:
            return ResultPayload(success=False, error=["Invalid format for journal"])
        path = CONFIG_DIR / ramble
        page = ramble
        CONFIG_FILE_PATH = path / f"{ramble}.yml"

    try:
        is_safe_path(CONFIG_FILE_PATH, team)
    except (PermissionError, FileNotFoundError, RuntimeError) as e:
        return ResultPayload(success=False, error=[str(e)])

    base_text = f"""title: {page}
concept:
what:
why:
how:
scripts:
"""
    messages = []
    if not path.exists():
        path.mkdir(parents=True, exist_ok=True)
        messages.append(f"Created new journal: {path.name}!")

    if not CONFIG_FILE_PATH.exists():
        with open(CONFIG_FILE_PATH, "x") as f:
            f.write(base_text)
        messages.append(f"Page {page} created!")
    else:
        if not payload.confirmed:
            return ResultPayload(success=False, error=["Creation aborted by user."])

    return ResultPayload(
        success=True,
        message=messages,
        data={
            "file_to_edit": str(CONFIG_FILE_PATH),
            "should_encrypt": should_encrypt,
            "target": ramble,
        },
    )


def gatherEditRamble(payload: RambleEditPayload) -> DataGatherRequest | None:
    """If a journal is passed, returns a DataGatherRequest for page selection.

    Args:
        payload (RambleEditPayload): Context for editing a ramble.

    Returns:
        DataGatherRequest | None: Request prompting for the page to edit, or None if valid file format supplied.
    """
    ramble = payload.target
    if ".." in ramble or "/" in ramble:
        return None
    if "." in ramble:
        return None

    team = payload.context.team
    try:
        CONFIG_DIR = _get_ramble_dir(team)
    except (ValueError, FileNotFoundError):
        return None
    path = CONFIG_DIR / ramble

    if path.exists() and path.is_dir():
        entries = sorted([f.name for f in path.iterdir() if f.is_file()])
        if entries:
            choices = [Path(e).stem for e in entries]
            return DataGatherRequest(
                name="ramble_edit_select",
                fields=[
                    DataGatherPayload(
                        name="selected_page",
                        prompt=f"Which page do you want to edit in journal '{ramble}'?",
                        input_type="choice",
                        choices=choices,
                        required=True,
                    )
                ],
            )
    return None


def handleEditRamble(payload: RambleEditPayload) -> ResultPayload[dict[str, Any]]:
    """Prepares editing of an existing ramble journal or page, returning info for the interface to handle it.

    Args:
        payload (RambleEditPayload): Details on what to edit and encryption state context.

    Returns:
        ResultPayload[dict[str, Any]]: The result holding the requested file's path and its encryptability state.
    """

    from omegaconf import DictConfig, OmegaConf

    ramble = payload.target
    if ".." in ramble or "/" in ramble:
        return ResultPayload(success=False, error=["Invalid format for ramble."])

    team = payload.context.team
    try:
        CONFIG_DIR = _get_ramble_dir(team)
    except (ValueError, FileNotFoundError) as e:
        return ResultPayload(success=False, error=[str(e)])

    GLOBAL_CONFIG_DIR = Path(
        os.getenv("CHAOS_CONFIG_DIR", Path.home() / ".config" / "chaos")
    )
    GLOBAL_CONFIG_FILE_PATH = os.path.join(GLOBAL_CONFIG_DIR, "config.yml")
    global_config = OmegaConf.create()
    if os.path.exists(GLOBAL_CONFIG_FILE_PATH):
        global_config = OmegaConf.load(GLOBAL_CONFIG_FILE_PATH) or OmegaConf.create()
    global_config = cast(DictConfig, global_config)

    sops_file_override = payload.context.sops_file_override or global_config.get(
        "sops_file"
    )

    if "." in ramble:
        parts = ramble.split(".", 1)
        directory = parts[0]
        page = parts[1] if parts[1] else directory
        file_path = CONFIG_DIR / directory / f"{page}.yml"
    else:
        return ResultPayload(
            success=False, error=[f"Ambiguous ramble target: {ramble}"]
        )

    try:
        if not file_path.exists():
            is_safe_path(file_path.parent, team)
            return ResultPayload(
                success=False, error=[f"Ramble page not found: {file_path}"]
            )
        is_safe_path(file_path, team)
    except (PermissionError, FileNotFoundError, RuntimeError) as e:
        return ResultPayload(success=False, error=[str(e)])

    is_encrypted = False
    try:
        data = OmegaConf.load(file_path)
        if "sops" in data:
            is_encrypted = True
    except Exception:
        pass

    return ResultPayload(
        success=True,
        data={
            "file_path": str(file_path),
            "is_encrypted": is_encrypted,
            "sops_config": sops_file_override,
            "edit_sops_file": payload.edit_sops_file,
        },
    )


def handleEncryptRamble(payload: RambleEncryptPayload) -> ResultPayload[None]:
    """Encrypts specified keys in a ramble page using sops.

    Args:
        payload (RambleEncryptPayload): The payload outlining the ramble to encrypt and which keys specifically.

    Returns:
        ResultPayload[None]: A payload summarizing encryption state messages or failure.

    Notes:
        If -k not passed, encrypts everything except base keys.
        The tags key is never encrypted, helping to optimize searching.
    """

    from omegaconf import DictConfig, OmegaConf

    GLOBAL_CONFIG_DIR = Path(
        os.getenv("CHAOS_CONFIG_DIR", Path.home() / ".config" / "chaos")
    )
    GLOBAL_CONFIG_FILE_PATH = os.path.join(GLOBAL_CONFIG_DIR, "config.yml")
    global_config = OmegaConf.create()
    if os.path.exists(GLOBAL_CONFIG_FILE_PATH):
        global_config = OmegaConf.load(GLOBAL_CONFIG_FILE_PATH) or OmegaConf.create()
    global_config = cast(DictConfig, global_config)

    sops_file_override = payload.context.sops_file_override or global_config.get(
        "sops_file"
    )

    if not sops_file_override:
        return ResultPayload(
            success=False,
            error=[
                "You need a sops configuration for encryption to work.\n"
                "   Provide one with '-ss /path/to/.sops.yml' or set a default with 'chaos set sops /path/to/.sops.yml'."
            ],
        )
    try:
        if is_vault_in_use(sops_file_override):
            is_authed, message = check_vault_auth()
            if not is_authed:
                return ResultPayload(success=False, error=[message])

        ramble = payload.target
        if ".." in ramble or "/" in ramble:
            return ResultPayload(success=False, error=["Invalid format for ramble."])

        keys = payload.keys or []
        team = payload.context.team

        CONFIG_DIR = _get_ramble_dir(team)

        if "." not in ramble:
            return ResultPayload(
                success=False,
                error=[
                    "You must pass a specific page to be encrypted (e.g., diary.page)."
                ],
            )

        parts = ramble.split(".", 1)
        directory = parts[0]
        page = parts[1]
        path = CONFIG_DIR / directory
        fullPath = path / f"{page}.yml"

        is_safe_path(fullPath, team)

        if not fullPath.exists():
            return ResultPayload(
                success=False, error=[f"Ramble page not found: {fullPath}"]
            )

        data = OmegaConf.load(fullPath)

        keysInData = data.keys()
        baseKeys = ["title", "concept", "sops", "tags"]
        if not keys:
            keys = [str(key) for key in keysInData if key not in baseKeys]

        if not keys:
            return ResultPayload(success=True, message=["No new keys to encrypt."])

        escaped_keys = [re.escape(str(key)) for key in keys]
        joinKeys = "|".join(escaped_keys)
        regex = f"^({joinKeys})$"

        if "sops" in data:
            new_context = SecretsContext(
                team=payload.context.team,
                sops_file_override=payload.context.sops_file_override,
                secrets_file_override=str(fullPath),
                provider_config=payload.context.provider_config,
                i_know_what_im_doing=payload.context.i_know_what_im_doing,
            )
            result = decrypt_secrets(
                str(fullPath), sops_file_override, global_config, new_context
            )

            import platform
            from contextlib import ExitStack

            from chaos.lib.secret_backends.providers.ephemeral import mac_ram_disk

            is_mac = platform.system() == "Darwin"

            with ExitStack() as stack:
                if is_mac:
                    shm_dir = stack.enter_context(mac_ram_disk())
                else:
                    shm_dir = "/dev/shm" if os.path.exists("/dev/shm") else None

                with tempfile.NamedTemporaryFile(
                    mode="w", delete=False, dir=shm_dir, suffix=".yml"
                ) as tmp:
                    os.chmod(tmp.name, 0o600)
                    tmp.write(result)
                    tmpPath = tmp.name

                try:
                    subprocess.run(
                        [
                            "sops",
                            "--config",
                            sops_file_override,
                            "--filename-override",
                            str(fullPath),
                            "--encrypt",
                            "--in-place",
                            "--encrypted-regex",
                            regex,
                            str(tmpPath),
                        ],
                        check=True,
                    )
                    shutil.move(tmpPath, fullPath)
                finally:
                    if os.path.exists(tmpPath):
                        os.remove(tmpPath)
        else:
            subprocess.run(
                [
                    "sops",
                    "--config",
                    sops_file_override,
                    "--encrypt",
                    "--in-place",
                    "--encrypted-regex",
                    regex,
                    str(fullPath),
                ],
                check=True,
            )

        return ResultPayload(
            success=True, message=[f"Successfully encrypted keys in {ramble}"]
        )
    except (
        ValueError,
        PermissionError,
        FileNotFoundError,
        RuntimeError,
        Exception,
    ) as e:
        if isinstance(e, FileNotFoundError):
            return ResultPayload(
                success=False,
                error=[
                    "The `sops` command was not found. Please install sops to encrypt rambles."
                ],
            )
        if isinstance(e, subprocess.CalledProcessError):
            return ResultPayload(
                success=False, error=[f"Ramble encryption/decryption failed: {e}"]
            )
        return ResultPayload(success=False, error=[str(e)])


def handleReadRamble(payload: RambleReadPayload) -> ResultPayload[dict[str, Any]]:
    """Reads the content of specified rambles and returns them.

    Args:
        payload (RambleReadPayload): Contains targets and state required to retrieve rambles.

    Returns:
        ResultPayload[dict[str, Any]]: A payload wrapping the read content for matching rambles.
    """

    from omegaconf import DictConfig, OmegaConf

    GLOBAL_CONFIG_DIR = Path(
        os.getenv("CHAOS_CONFIG_DIR", Path.home() / ".config" / "chaos")
    )

    GLOBAL_CONFIG_FILE_PATH = os.path.join(GLOBAL_CONFIG_DIR, "config.yml")
    global_config = OmegaConf.create()
    if os.path.exists(GLOBAL_CONFIG_FILE_PATH):
        global_config = OmegaConf.load(GLOBAL_CONFIG_FILE_PATH) or OmegaConf.create()
    global_config = cast(DictConfig, global_config)

    sops_file_override = payload.context.sops_file_override or global_config.get(
        "sops_file"
    )

    results = {}
    try:
        CONFIG_DIR = _get_ramble_dir(payload.context.team)
    except (ValueError, FileNotFoundError) as e:
        return ResultPayload(success=False, error=[str(e)])

    for target in payload.targets:
        if "." not in target:
            continue

        parts = target.split(".", 1)
        journal = parts[0]
        page = parts[1]
        full_path = CONFIG_DIR / journal / f"{page}.yml"

        try:
            ramble_data, _ = _read_ramble_content(
                full_path, sops_file_override, payload.context, global_config
            )
            results[target] = OmegaConf.to_container(ramble_data, resolve=True)
        except Exception as e:
            return ResultPayload(success=False, error=[str(e)])

    return ResultPayload(success=True, data=results)


def handleFindRamble(payload: RambleFindPayload) -> ResultPayload[list[str]]:
    """Searches for rambles containing a specific term, optionally filtered by tag.

    Args:
        payload (RambleFindPayload): Definition of constraints to find target rambles.

    Returns:
        ResultPayload[list[str]]: The list of matches, or an appropriate error response.

    Notes:
        If nothing passed, lists all rambles.
    """

    from omegaconf import DictConfig, OmegaConf

    from chaos.lib.args.dataclasses import ResultPayload

    team = payload.context.team

    try:
        RAMBLE_DIR = _get_ramble_dir(team)
    except (ValueError, FileNotFoundError) as e:
        return ResultPayload(success=False, error=[str(e)])

    search_term = payload.find_term
    required_tag = payload.tag
    results = []
    warnings = []

    GLOBAL_CONFIG_DIR = Path(
        os.getenv("CHAOS_CONFIG_DIR", Path.home() / ".config" / "chaos")
    )

    GLOBAL_CONFIG_FILE_PATH = os.path.join(GLOBAL_CONFIG_DIR, "config.yml")
    global_config = {}
    if os.path.exists(GLOBAL_CONFIG_FILE_PATH):
        global_config = OmegaConf.load(GLOBAL_CONFIG_FILE_PATH) or OmegaConf.create()

    global_config = cast(DictConfig, global_config)

    sops_file_override = payload.context.sops_file_override or global_config.get(
        "sops_file"
    )

    for ramble_file in RAMBLE_DIR.rglob("*.yml"):
        try:
            if search_term and required_tag:
                bare_data = OmegaConf.load(ramble_file)
                bare_data = cast(DictConfig, bare_data)
                tags = bare_data.get("tags", [])
                if required_tag not in tags:
                    continue

                data, text = _read_ramble_content(
                    ramble_file, sops_file_override, payload.context, global_config
                )

                if search_term and search_term.lower() not in text.lower():
                    continue

            elif search_term:
                data, text = _read_ramble_content(
                    ramble_file, sops_file_override, payload.context, global_config
                )

                if search_term and search_term.lower() not in text.lower():
                    continue

            elif required_tag:
                data = cast(DictConfig, OmegaConf.load(ramble_file))
                tags = data.get("tags", [])
                if required_tag not in tags:
                    continue

            ramble = ramble_file.parent.name
            page = ramble_file.stem
            results.append(f"{ramble}.{page}")
        except Exception as e:
            warnings.append(
                f"Skipping {ramble_file.relative_to(RAMBLE_DIR)} due to error: {e}"
            )
            continue

    if not results:
        return ResultPayload(
            success=True,
            data=[],
            message=["Could not find any rambles."],
            error=warnings,
        )

    return ResultPayload(success=True, data=results, message=warnings)


def handleMoveRamble(payload: RambleMovePayload) -> ResultPayload[None]:
    """Moves or renames a ramble journal or page.

    Args:
        payload (RambleMovePayload): Context describing the origin point, and intended target point.

    Returns:
        ResultPayload[None]: Status payload of the operation.
    """
    team = payload.context.team
    old = payload.old
    new = payload.new

    try:
        RAMBLE_DIR = _get_ramble_dir(team)

        if ".." in old or "/" in old or ".." in new or "/" in new:
            return ResultPayload(success=False, error=["Invalid format for ramble."])

        old_is_dir = "." not in old
        new_is_dir = "." not in new

        try:
            source_path = (
                RAMBLE_DIR / old
                if old_is_dir
                else RAMBLE_DIR / old.split(".", 1)[0] / f"{old.split('.', 1)[1]}.yml"
            )
        except IndexError:
            return ResultPayload(
                success=False, error=[f"Invalid source format: '{old}'"]
            )

        is_safe_path(source_path, team)

        dest_dir_path = (
            RAMBLE_DIR / new if new_is_dir else RAMBLE_DIR / new.split(".", 1)[0]
        )
        dest_file_path = (
            None if new_is_dir else dest_dir_path / f"{new.split('.', 1)[1]}.yml"
        )

        is_safe_path(dest_dir_path, team)
        if dest_file_path:
            is_safe_path(dest_file_path, team)

        if not source_path.exists():
            return ResultPayload(
                success=False, error=[f"No such journal or page: {source_path}"]
            )

        if dest_file_path is None or dest_dir_path is None:
            return ResultPayload(
                success=False, error=["Destination path could not be determined."]
            )

        message = ""
        if old_is_dir and new_is_dir:
            if dest_dir_path.exists():
                return ResultPayload(
                    success=False,
                    error=[
                        f"Destination journal (directory) already exists: {dest_dir_path}"
                    ],
                )
            shutil.move(str(source_path), str(dest_dir_path))
            message = f"Successfully moved journal '{old}' to '{new}'"

        elif not old_is_dir and not new_is_dir:
            if dest_file_path.exists():
                return ResultPayload(
                    success=False,
                    error=[f"Destination page (file) already exists: {dest_file_path}"],
                )

            dest_file_path.parent.mkdir(parents=True, exist_ok=True)

            shutil.move(str(source_path), str(dest_file_path))
            message = f"Successfully moved page '{old}' to '{new}'"

        elif old_is_dir and not new_is_dir:
            return ResultPayload(
                success=False, error=["Cannot move a directory to a singular file."]
            )

        elif not old_is_dir and new_is_dir:
            final_dest_file = dest_dir_path / source_path.name
            is_safe_path(final_dest_file, team)
            if final_dest_file.exists():
                return ResultPayload(
                    success=False,
                    error=[
                        f"Page (file) '{source_path.name}' already exists in journal '{new}'"
                    ],
                )
            dest_dir_path.mkdir(parents=True, exist_ok=True)
            shutil.move(str(source_path), str(final_dest_file))
            new_ramble_name = f"{new}.{source_path.stem}"
            message = f"Successfully moved page '{old}' to '{new_ramble_name}'"

    except (
        ValueError,
        FileNotFoundError,
        FileExistsError,
        PermissionError,
        RuntimeError,
    ) as e:
        return ResultPayload(success=False, error=[str(e)])

    return ResultPayload(success=True, message=[message])


def gatherDelRamble(payload: RambleDeletePayload) -> DataGatherRequest | None:
    """Returns a DataGatherRequest for confirming the deletion of a ramble or journal.

    Args:
        payload (RambleDeletePayload): Represents context parameters necessary for deletion process.

    Returns:
        DataGatherRequest | None: Object representation defining prompt requirement or None.
    """
    ramble = payload.ramble
    return DataGatherRequest(
        name="ramble_delete",
        fields=[
            DataGatherPayload(
                name="confirm_delete",
                prompt=f"Are you sure you want to delete {ramble}?",
                input_type="boolean",
                required=True,
            )
        ],
    )


def handleDelRamble(payload: RambleDeletePayload) -> ResultPayload[None]:
    """Deletes a ramble journal or page.

    Args:
        payload (RambleDeletePayload): The confirmed target payload state.

    Returns:
        ResultPayload[None]: The status payload regarding operation's termination status.
    """
    if not payload.confirmed:
        return ResultPayload(success=False, error=["Deletion not confirmed by user."])

    team = payload.context.team
    ramble = payload.ramble

    try:
        RAMBLE_DIR = _get_ramble_dir(team)

        if ".." in ramble or "/" in ramble:
            return ResultPayload(success=False, error=["Invalid format for ramble."])

        if "." in ramble:
            parts = ramble.split(".", 1)
            journal = parts[0]
            page = parts[1]
            rambleFile = RAMBLE_DIR / journal / f"{page}.yml"
            is_safe_path(rambleFile, team)
            if not rambleFile.exists():
                return ResultPayload(
                    success=False, error=[f"{rambleFile} does not exist."]
                )

            os.remove(rambleFile)
            return ResultPayload(success=True, message=[f"Removed page {ramble}."])
        else:
            ramblePath = RAMBLE_DIR / ramble
            is_safe_path(ramblePath, team)
            if not ramblePath.exists():
                return ResultPayload(
                    success=False, error=[f"{ramblePath} does not exist."]
                )

            shutil.rmtree(ramblePath)
            return ResultPayload(success=True, message=[f"Removed journal {ramble}."])

    except (
        ValueError,
        FileNotFoundError,
        FileExistsError,
        PermissionError,
        RuntimeError,
    ) as e:
        return ResultPayload(success=False, error=[str(e)])


def handleUpdateEncryptRamble(
    payload: RambleUpdateEncryptPayload,
) -> ResultPayload[None]:
    """Updates encryption keys for all encrypted rambles in the ramble directory.

    Args:
        payload (RambleUpdateEncryptPayload): Details regarding environment needed to update everything.

    Returns:
        ResultPayload[None]: Response mapping successes and errors of the operation.
    """

    from omegaconf import DictConfig, OmegaConf

    team = payload.context.team
    updated_count = 0
    messages = []
    warnings = []

    try:
        RAMBLE_DIR = _get_ramble_dir(team)

        GLOBAL_CONFIG_DIR = Path(
            os.getenv("CHAOS_CONFIG_DIR", Path.home() / ".config" / "chaos")
        )

        GLOBAL_CONFIG_FILE_PATH = os.path.join(GLOBAL_CONFIG_DIR, "config.yml")
        global_config = {}

        if os.path.exists(GLOBAL_CONFIG_FILE_PATH):
            global_config = (
                OmegaConf.load(GLOBAL_CONFIG_FILE_PATH) or OmegaConf.create()
            )
        global_config = cast(DictConfig, global_config)

        sops_file_override = payload.context.sops_file_override or global_config.get(
            "sops_file"
        )

        if sops_file_override and is_vault_in_use(sops_file_override):
            is_authed, message = check_vault_auth()
            if not is_authed:
                return ResultPayload(success=False, error=[message])

        context = _handle_provider_arg(payload.context, global_config)
        provider = _getProvider(context, global_config)

        for ramble_file in RAMBLE_DIR.rglob("*.yml"):
            is_safe_path(ramble_file, team)
            try:
                data = OmegaConf.load(ramble_file)
                if "sops" in data:
                    if not sops_file_override:
                        raise ValueError(
                            "An encrypted ramble was found, but no sops configuration was provided.\n"
                            "   Provide one with '-ss /path/to/.sops.yml' or set a default with 'chaos set sops /path/to/.sops.yml'."
                        )

                    messages.append(
                        f"Checking for key updates in {ramble_file.relative_to(RAMBLE_DIR)}..."
                    )
                    if provider:
                        provider.updatekeys(str(ramble_file), sops_file_override)
                    else:
                        subprocess.run(
                            [
                                "sops",
                                "--config",
                                sops_file_override,
                                "updatekeys",
                                "-y",
                                str(ramble_file),
                            ],
                            capture_output=True,
                            text=True,
                            check=True,
                        )
                    updated_count += 1
            except Exception as e:
                if isinstance(e, subprocess.CalledProcessError):
                    raise RuntimeError(
                        f"Ramble key update with sops failed for {ramble_file}.\n{e.stderr}"
                    ) from e
                if isinstance(e, FileNotFoundError):
                    raise FileNotFoundError(
                        "`sops` command not found. Please ensure sops is installed and in your PATH."
                    )
                warnings.append(
                    f"Could not read or parse ramble file: {ramble_file}. Skipping."
                )
                continue
    except (
        ValueError,
        FileNotFoundError,
        FileExistsError,
        PermissionError,
        RuntimeError,
    ) as e:
        return ResultPayload(success=False, error=[str(e)])

    final_msg = ""
    if updated_count > 0:
        final_msg = f"Processed {updated_count} encrypted ramble(s)."
    else:
        final_msg = "No encrypted ramble files found to update."

    return ResultPayload(success=True, message=messages + [final_msg], error=warnings)
