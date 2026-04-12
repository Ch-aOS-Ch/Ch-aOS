import os
import subprocess
import sys
from pathlib import Path
from typing import Any, cast

import requests
from omegaconf import DictConfig, OmegaConf

from chaos.lib.args.dataclasses import ResultPayload, StyxPayload

TIMEOUT = 10


def get_styx_registry(payload: StyxPayload) -> tuple[str | None, str | None]:
    """Fetches the Styx registry data from the specified URL.

    Returns:
        tuple[str | None, str | None]: A tuple containing the registry data (str) and an error message (str), if applicable.
    """
    url = getattr(
        payload,
        "registry_url",
        os.getenv(
            "CHAOS_STYX_REGISTRY",
            "https://raw.githubusercontent.com/Ch-aOS-Ch/styx/main/registry.yaml",
        ),
    )
    try:
        response = requests.get(url, stream=True, timeout=TIMEOUT)
        response.raise_for_status()
        return response.text, None
    except requests.RequestException as e:
        return None, f"Error fetching Styx registry: {e}"


def parse_styx_registry(
    registry_data: str, registry_names: list[str]
) -> tuple[list[dict], list[str]]:
    """Parses the Styx registry data.

    Args:
        registry_data (str): The raw string data of the registry YAML.
        registry_names (list[str]): The list of specific registry names to parse.

    Returns:
        tuple[list[dict], list[str]]: A tuple of matched entries and a list of parsing errors.
    """
    if not registry_data:
        return [], ["No registry data provided."]

    errors = []
    try:
        parsed_data = OmegaConf.create(registry_data)
        parsed_data = cast(DictConfig, parsed_data)
    except Exception as e:
        return [], [f"Error parsing YAML: {e}"]

    if "styx" not in parsed_data:
        return [], ["Invalid registry format: 'styx' key not found."]

    styx_entries = parsed_data.styx
    entries = []

    for name in registry_names:
        if name not in styx_entries:
            errors.append(f"Registry name '{name}' not found in Styx registry.")
            continue

        name_data = styx_entries.get(name)
        name_data["registry_name"] = name
        entries.append(name_data)

    return entries, errors


def _check_hash(
    file_path: Path, expected_hash: str
) -> tuple[bool, str | None, str | None]:
    """Checks if the file at file_path matches the expected SHA-256 hash.

    Args:
        file_path (Path): Path to the local file to check.
        expected_hash (str): The expected SHA-256 hash.

    Returns:
        tuple[bool, str | None, str | None]: A tuple containing a boolean of the match result, the calculated hash, and an error string if applicable.
    """
    from hashlib import sha256

    sha256_hash = sha256()
    try:
        with open(file_path, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)

        calculated_hash = sha256_hash.hexdigest()

        return calculated_hash == expected_hash, calculated_hash, None
    except Exception as e:
        return False, None, f"Error checking hash for {file_path}: {e}"


def install_styx_entries(payload: StyxPayload) -> ResultPayload[None]:
    """Installs the given Styx registry entries.

    Args:
        payload (StyxPayload): The structured payload containing the list of registry entries to install and the force flag.

    Returns:
        ResultPayload[None]: The status payload regarding the operation's outcome.
    """
    entries = payload.entries
    force = payload.force
    messages = []
    errors = []

    raw_registry, error = get_styx_registry(payload)
    if error:
        return ResultPayload(success=False, error=[error])
    if not raw_registry:
        return ResultPayload(success=False, error=["Failed to retrieve Styx registry."])

    parsed_entries, parse_errors = parse_styx_registry(raw_registry, entries)
    errors.extend(parse_errors)

    for entry in parsed_entries:
        url = entry.get("repo")
        tag_version = entry.get("version")
        pkg_name = entry.get("name")
        expected_hash = entry.get("hash", "")

        if not expected_hash or len(expected_hash) != 64:
            errors.append(
                f"Invalid or missing hash for '{pkg_name}'. Skipping package."
            )
            continue

        if not pkg_name:
            errors.append("Skipping entry with missing name.")
            continue

        if not tag_version:
            errors.append(f"Skipping '{pkg_name}': Missing version.")
            continue

        if not url or not tag_version:
            errors.append(f"Skipping '{pkg_name}': Missing repo URL or version.")
            continue

        clean_version = tag_version.lstrip("v")

        normalized_name = pkg_name.replace("-", "_")
        wheel_remote_name = f"{normalized_name}-{clean_version}-py3-none-any.whl"

        download_url = f"{url}/releases/download/{tag_version}/{wheel_remote_name}"

        wheel_local_filename = f"{pkg_name}.whl"

        try:
            dir_name = Path(
                os.getenv(
                    "CHAOS_PLUGIN_DIR",
                    Path.home() / ".local" / "share" / "chaos" / "plugins",
                )
            )
            dir_name.mkdir(parents=True, exist_ok=True)

            local_path = dir_name / wheel_local_filename
            tmp_path = dir_name / f"{wheel_local_filename}.tmp"

            if local_path.exists() and not force:
                messages.append(f"Plugin '{pkg_name}' is already installed.")
                continue

            messages.append(f"Downloading {pkg_name} ({tag_version})...")

            with requests.get(download_url, stream=True, timeout=30) as response:
                response.raise_for_status()

                if ".." in wheel_local_filename or "/" in wheel_local_filename:
                    raise ValueError("Security violation in filename")

                with open(tmp_path, "wb") as wheel_file:
                    for chunk in response.iter_content(chunk_size=8192):
                        wheel_file.write(chunk)

                is_correct, calculated_hash, hash_error = _check_hash(
                    tmp_path, expected_hash
                )

                if hash_error:
                    errors.append(hash_error)
                    tmp_path.unlink(missing_ok=True)
                    continue

                if not is_correct:
                    tmp_path.unlink(missing_ok=True)  # Apaga o lixo
                    errors.append(
                        f"Hash mismatch for '{pkg_name}'. Expected: {expected_hash}, Calculated: {calculated_hash}. Download may be corrupted or tampered with."
                    )
                    continue

                valid_whl_name = dir_name / wheel_remote_name
                tmp_path.rename(valid_whl_name)

                pip_cmd = [
                    sys.executable,
                    "-m",
                    "pip",
                    "install",
                    "--no-cache-dir",
                    "--disable-pip-version-check",
                    "--target",
                    str(dir_name),
                    str(valid_whl_name),
                ]

                try:
                    subprocess.run(pip_cmd, capture_output=True, text=True, check=True)
                    messages.append(
                        f"Successfully installed '{pkg_name}' version {tag_version}."
                    )
                except subprocess.CalledProcessError as e:
                    raw_stderr = e.stderr.strip() if e.stderr else str(e)
                    errors.append(
                        f"Error installing '{pkg_name}' with pip: {raw_stderr}"
                    )
                    continue
                finally:
                    valid_whl_name.unlink(missing_ok=True)

        except requests.exceptions.HTTPError as e:
            if e.response is not None and e.response.status_code == 404:
                errors.append(
                    f"Error: Release not found at {download_url}. Check if the wheel name matches format: {wheel_remote_name}"
                )
            else:
                errors.append(f"HTTP Error installing {pkg_name}: {e}")
        except Exception as e:
            errors.append(f"Error installing {pkg_name}: {e}")

    try:
        from chaos.lib.plugDiscovery import get_plugins

        get_plugins(update_cache=True)
    except ImportError:
        errors.append("Warning: Could not reload plugins cache (module not found).")

    success = len(errors) == 0 or len(messages) > 0
    return ResultPayload(success=success, message=messages, error=errors)


def list_styx_entries(payload: StyxPayload) -> ResultPayload[dict[str, Any]]:
    """Lists the available Styx registry entries.

    Args:
        payload (StyxPayload): The structured payload containing the list of registry entries to display.

    Returns:
        ResultPayload[dict[str, Any]]: A payload containing matched registry details.
    """
    entries = payload.entries
    raw_registry, error = get_styx_registry(payload)
    if error:
        return ResultPayload(success=False, error=[error])
    if not raw_registry:
        return ResultPayload(
            success=False, error=["Could not fetch Styx registry data."]
        )

    try:
        registry_data = OmegaConf.create(raw_registry)
        registry_data = cast(DictConfig, registry_data)
    except Exception as e:
        return ResultPayload(success=False, error=[f"Error parsing YAML: {e}"])

    if "styx" not in registry_data:
        return ResultPayload(
            success=False, error=["Invalid registry format: 'styx' key not found."]
        )

    styx_entries = registry_data.styx
    keys_to_show = entries if entries else list(styx_entries.keys())

    output_data = {}
    errors = []
    for name in keys_to_show:
        if name in styx_entries:
            output_data[name] = styx_entries[name]
        else:
            errors.append(f"Registry entry '{name}' not found.")

    return ResultPayload(success=True, data=output_data, error=errors)


def uninstall_styx_entries(entries: list[str]) -> ResultPayload[None]:
    """Uninstalls the given Styx registry entries using pip.

    Args:
        entries (list[str]): The list of registry entries to uninstall.

    Returns:
        ResultPayload[None]: A payload summarizing the deletion state.
    """
    messages = []
    errors = []

    plugin_dir = Path(
        os.getenv(
            "CHAOS_PLUGIN_DIR", Path.home() / ".local" / "share" / "chaos" / "plugins"
        )
    )

    if not plugin_dir.exists():
        return ResultPayload(success=False, error=["Plugin directory does not exist."])

    env = os.environ.copy()
    env["PYTHONPATH"] = str(plugin_dir) + os.pathsep + env.get("PYTHONPATH", "")

    for name in entries:
        pip_cmd = [
            sys.executable,
            "-m",
            "pip",
            "uninstall",
            "-y",
            name,
        ]

        try:
            result = subprocess.run(
                pip_cmd,
                env=env,
                capture_output=True,
                text=True,
                check=False,
            )

            # Since Pip returns 0 even if the package is not found, we need to check
            # the output ourselves.
            output = result.stdout + result.stderr

            if "Successfully uninstalled" in output:
                messages.append(f"Successfully uninstalled '{name}'.")
            elif "WARNING: Skipping" in output and "as it is not installed" in output:
                errors.append(f"Plugin '{name}' not found or already uninstalled.")
            elif result.returncode != 0:
                errors.append(f"Error uninstalling '{name}': {output.strip()}")
            else:
                messages.append(
                    f"Uninstallation of '{name}' completed with ambiguous output from pip."
                )

        except FileNotFoundError:
            errors.append(
                f"Error: Command '{sys.executable}' not found. Cannot run pip."
            )
            break
        except Exception as e:
            errors.append(
                f"An unexpected error occurred while uninstalling '{name}': {e}"
            )

    try:
        from chaos.lib.plugDiscovery import get_plugins

        get_plugins(update_cache=True)
        messages.append("Plugin cache updated.")
    except ImportError:
        errors.append("Warning: Could not reload plugins cache (module not found).")

    success = not any("Error" in e for e in errors)
    return ResultPayload(success=success, message=messages, error=errors)


def handle_styx(payload: StyxPayload) -> ResultPayload[dict[str, Any] | None]:
    """Handles parsing and routing for the specified styx subcommands.

    Args:
        payload (StyxPayload): The structured payload containing the requested action and corresponding details.

    Returns:
        ResultPayload[dict[str, Any] | None]: The generic result of the styx operation.
    """
    try:
        match payload.styx_commands:
            case "invoke":
                return install_styx_entries(payload)

            case "list":
                return list_styx_entries(payload)

            case "destroy":
                return uninstall_styx_entries(payload.entries)
            case _:
                return ResultPayload(
                    success=False, error=["Unsupported styx subcommand."]
                )
    except (ValueError, FileNotFoundError, RuntimeError, EnvironmentError) as e:
        return ResultPayload(success=False, error=[str(e)])
