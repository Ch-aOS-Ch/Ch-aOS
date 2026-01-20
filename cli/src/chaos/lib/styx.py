import os
from pathlib import Path
from typing import cast
import requests
from omegaconf import DictConfig, OmegaConf

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

    if 'styx' not in registry_data:
        print("Invalid registry format: 'styx' key not found.")
        return []

    styx_entries = registry_data.styx
    entries = []

    for name in registry_names:
        if name not in styx_entries:
            print(f"Registry name '{name}' not found in Styx registry.")
            continue

        name_data = styx_entries.get(name)
        name_data['registry_name'] = name
        entries.append(name_data)

    return entries

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
        url = entry.get('repo')
        tag_version = entry.get('version')
        pkg_name = entry.get('name')

        if not pkg_name:
            print("Skipping entry with missing name.")
            continue

        if not tag_version:
            print(f"Skipping '{pkg_name}': Missing version.")
            continue

        if not url or not tag_version:
            print(f"Skipping '{pkg_name}': Missing repo URL or version.")
            continue

        clean_version = tag_version.lstrip('v')

        normalized_name = pkg_name.replace('-', '_')
        wheel_remote_name = f"{normalized_name}-{clean_version}-py3-none-any.whl"

        download_url = f"{url}/releases/download/{tag_version}/{wheel_remote_name}"

        wheel_local_filename = f"{pkg_name}.whl"

        try:
            dir_name = Path(os.path.expanduser("~/.local/share/chaos/plugins"))
            dir_name.mkdir(parents=True, exist_ok=True)
            local_path = dir_name / wheel_local_filename

            if local_path.exists() and not force:
                print(f"Plugin '{pkg_name}' is already installed.")
                continue

            print(f"Downloading {pkg_name} ({tag_version})...")

            with requests.get(download_url, stream=True, timeout=30) as response:
                response.raise_for_status()

                if ".." in wheel_local_filename or "/" in wheel_local_filename:
                    raise ValueError("Security violation in filename")

                with open(local_path, "wb") as wheel_file:
                    for chunk in response.iter_content(chunk_size=8192):
                        wheel_file.write(chunk)

            try:
                from chaos.lib.plugDiscovery import get_plugins
                get_plugins(update_cache=True)
            except ImportError:
                print("Warning: Could not reload plugins cache (module not found).")

            print(f"Successfully installed '{pkg_name}' version {tag_version}.")

        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 404:
                print(f"Error: Release not found at {download_url}. Check if the wheel name matches format: {wheel_remote_name}")
            else:
                print(f"HTTP Error installing {pkg_name}: {e}")
        except Exception as e:
            print(f"Error installing {pkg_name}: {e}")

def list_styx_entries(entries: list[str] | None = None) -> str:
    """Lists the available Styx registry entries."""
    registry_text = get_styx_registry()
    if registry_text is None:
        return "Could not fetch Styx registry data."

    registry_data = OmegaConf.create(registry_text)

    if 'styx' not in registry_data:
        return "Invalid registry format."

    styx_entries = registry_data.styx

    keys_to_show = entries if entries else list(styx_entries.keys())

    output = []
    for name in keys_to_show:
        if name not in styx_entries:
            continue

        data = styx_entries[name]
        desc = data.get('about', 'No description')
        ver = data.get('version', 'unknown')
        repo = data.get('repo', '')

        if not repo:
            print(f"Warning: No repository URL for '{name}'.")
            continue

        output.append(f"{name} ({ver})\n   ├─ {desc}\n   └─ 🔗 {repo}")

    return "\n\n".join(output)

def uninstall_styx_entries(entries: list[str]):
    """Uninstalls the given Styx registry entries."""
    for name in entries:
        wheel_filename = f"{name}.whl"
        wheel_path = Path(os.path.expanduser(f"~/.local/share/chaos/plugins/{wheel_filename}"))

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
