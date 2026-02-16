import os
from pathlib import Path
from typing import cast

import requests
from omegaconf import DictConfig, OmegaConf

from chaos.lib.utils import validate_path

TIMEOUT = 10


def get_styx_registry():
    """Fetches the Styx registry data from the specified URL."""
    url = "https://raw.githubusercontent.com/Ch-aOS-Ch/styx/main/registry.yaml"
    try:
        response = requests.get(url, stream=True, timeout=TIMEOUT)
        response.raise_for_status()
        return response.text
    except requests.RequestException as e:
        print(f"[bold red]Error fetching Styx registry:[/] {e}")
        return None


def parse_styx_registry(registry_data, registry_names: list[str]) -> list[dict]:
    """Parses the Styx registry data and returns a list of entries."""
    if not registry_data:
        return []

    try:
        registry_data = OmegaConf.create(registry_data)
        registry_data = cast(DictConfig, registry_data)
    except Exception as e:
        print(f"Error parsing YAML: {e}")
        return []

    if "styx" not in registry_data:
        print("Invalid registry format: 'styx' key not found.")
        return []

    styx_entries = registry_data.styx
    entries = []

    for name in registry_names:
        if name not in styx_entries:
            print(f"Registry name '{name}' not found in Styx registry.")
            continue

        name_data = styx_entries.get(name)
        name_data["registry_name"] = name
        entries.append(name_data)

    return entries


def _check_hash(file_path: Path, expected_hash: str) -> tuple[bool, str | None]:
    """Checks if the file at file_path matches the expected SHA-256 hash."""
    from hashlib import sha256

    sha256_hash = sha256()
    try:
        with open(file_path, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)

        calculated_hash = sha256_hash.hexdigest()

        return calculated_hash == expected_hash, calculated_hash
    except Exception as e:
        print(f"Error checking hash for {file_path}: {e}")
        return False, None


def install_styx_entries(entries: list[str], force: bool = False):
    """
    Installs the given Styx registry entries.
    Args:
        entries: List of plugin names
        force: If True, overwrites existing plugins
    """
    raw_registry = get_styx_registry()
    if not raw_registry:
        return

    parsed_entries = parse_styx_registry(raw_registry, entries)

    for entry in parsed_entries:
        url = entry.get("repo")
        tag_version = entry.get("version")
        pkg_name = entry.get("name")
        expected_hash = entry.get("hash", "")

        if not expected_hash or len(expected_hash) != 64:
            print(
                f"Warning: Invalid or missing hash for '{pkg_name}'. Skipping package."
            )
            continue

        if not pkg_name:
            print("Skipping entry with missing name.")
            continue

        if not tag_version:
            print(f"Skipping '{pkg_name}': Missing version.")
            continue

        if not url or not tag_version:
            print(f"Skipping '{pkg_name}': Missing repo URL or version.")
            continue

        clean_version = tag_version.lstrip("v")

        normalized_name = pkg_name.replace("-", "_")
        wheel_remote_name = f"{normalized_name}-{clean_version}-py3-none-any.whl"

        download_url = f"{url}/releases/download/{tag_version}/{wheel_remote_name}"

        wheel_local_filename = f"{pkg_name}.whl"

        try:
            dir_name = Path(os.path.expanduser("~/.local/share/chaos/plugins"))
            dir_name.mkdir(parents=True, exist_ok=True)

            local_path = dir_name / wheel_local_filename
            tmp_path = dir_name / f"{wheel_local_filename}.tmp"

            if local_path.exists() and not force:
                print(f"Plugin '{pkg_name}' is already installed.")
                continue

            print(f"Downloading {pkg_name} ({tag_version})...")

            with requests.get(download_url, stream=True, timeout=30) as response:
                response.raise_for_status()

                if ".." in wheel_local_filename or "/" in wheel_local_filename:
                    raise ValueError("Security violation in filename")

                with open(tmp_path, "wb") as wheel_file:
                    for chunk in response.iter_content(chunk_size=8192):
                        wheel_file.write(chunk)

                is_correct, calculated_hash = _check_hash(tmp_path, expected_hash)

                if not is_correct:
                    tmp_path.unlink(missing_ok=True)  # Apaga o lixo
                    print(
                        f"Hash mismatch for '{pkg_name}'. Expected: {expected_hash}, Calculated: {calculated_hash}. Download may be corrupted or tampered with."
                    )
                    continue

                tmp_path.rename(local_path)

            print(f"Successfully installed '{pkg_name}' version {tag_version}.")

        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 404:
                print(
                    f"Error: Release not found at {download_url}. Check if the wheel name matches format: {wheel_remote_name}"
                )
            else:
                print(f"HTTP Error installing {pkg_name}: {e}")
        except Exception as e:
            print(f"Error installing {pkg_name}: {e}")

    try:
        from chaos.lib.plugDiscovery import get_plugins

        get_plugins(update_cache=True)
    except ImportError:
        print("Warning: Could not reload plugins cache (module not found).")


def list_styx_entries(
    entries: list[str] | None, no_pretty: bool, json_flag: bool
) -> str:
    """Lists the available Styx registry entries."""
    import json

    registry_text = get_styx_registry()
    if registry_text is None:
        return "Could not fetch Styx registry data."

    registry_data = OmegaConf.create(registry_text)

    if "styx" not in registry_data:
        return "Invalid registry format."

    styx_entries = registry_data.styx

    keys_to_show = entries if entries else list(styx_entries.keys())

    if no_pretty:
        output_data = {}
        for name in keys_to_show:
            if name in styx_entries:
                output_data[name] = styx_entries[name]

        if not output_data:
            return "{}" if json_flag else ""

        if json_flag:
            return json.dumps(
                OmegaConf.to_container(OmegaConf.create(output_data), resolve=True),
                indent=2,
            )
        else:
            return OmegaConf.to_yaml(OmegaConf.create(output_data))
    else:
        output = []
        for name in keys_to_show:
            if name not in styx_entries:
                continue

            data = styx_entries[name]
            desc = data.get("about", "No description")
            ver = data.get("version", "unknown")
            repo = data.get("repo", "")
            hash = data.get("hash", "")

            if not repo:
                print(f"Warning: No repository URL for '{name}'.")
                continue

            output.append(
                f"""{name} ({ver})
┬"""
                + "─" * (len(name) + 2 + len(ver))
                + f"""
├─ {desc}
├─ 🔗 {repo}
╰─ 🛡️ {hash[:8] + "..." + hash[-8:] if hash else "No hash provided"}
"""
            )

        return "\n\n".join(output)


def uninstall_styx_entries(entries: list[str]):
    """Uninstalls the given Styx registry entries."""
    for name in entries:
        wheel_filename = f"{name}.whl"
        validate_path(wheel_filename)

        wheel_path = Path(
            os.path.expanduser(f"~/.local/share/chaos/plugins/{wheel_filename}")
        )

        if not wheel_path.exists():
            print(f"Plugin '{name}' not found locally.")
            continue

        try:
            os.remove(wheel_path)
            print(f"Uninstalled '{name}'.")
        except Exception as e:
            print(f"Error uninstalling '{name}': {e}")

    try:
        from chaos.lib.plugDiscovery import get_plugins

        get_plugins(update_cache=True)
    except ImportError:
        pass
