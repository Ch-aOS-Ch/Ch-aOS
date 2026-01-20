import os
from pathlib import Path
import shutil
from typing import cast
import requests
from omegaconf import DictConfig, OmegaConf

def get_styx_registry():
    """Fetches the Styx registry data from the specified URL."""
    url = "https://raw.githubusercontent.com/Ch-aOS-Ch/styx/main/registy.yaml"

    try:
        response = requests.get(url, stream=True)
        response.raise_for_status()  # Raise an error for bad responses
        return response.text
    except requests.RequestException as e:
        print(f"Error fetching Styx registry: {e}")
        return None

def parse_styx_registry(registry_data, registry_names: list[str]) -> list[dict]:
    """Parses the Styx registry data and returns a list of entries."""
    registry_data = OmegaConf.create(registry_data)
    registry_data = cast(DictConfig, registry_data)

    if 'styx' not in registry_data:
        print("Invalid registry format: 'styx' key not found.")
        return []

    styx_entries = registry_data.styx
    entries = []
    for name in registry_names:
        if not name in styx_entries.keys():
            print(f"Registry name '{name}' not found in Styx registry.")
            continue

        name_data = styx_entries.get(name)
        entries.append(name_data)

    return entries

def install_styx_entries(entries: list[str]):
    """
    Installs the given Styx registry entries.

    Entries are recieved like so:
    styx:
      chaos-dots:
        name: chaos-dots
        repo: https://github.com/Ch-aOS-Ch/chaos-dots
        about: "A Ch-aotic dotfile manager, full with declarativity and statefulness"
        version: "v0.1.1"
    """
    parsed_entries = parse_styx_registry(get_styx_registry(), entries)
    for entry in parsed_entries:
        url = entry.get('repo')
        version = entry.get('version')
        if not url:
            print(f"Entry '{entry}' does not have a URL. Skipping installation.")
            continue

        if not version:
            print(f"Entry '{entry}' does not have a version specified. Skipping installation.")
            continue

        wheel_url = f"{url}/releases/download/{version}/{entry.get('name')}-{version}-py3-none-any.whl"
        try:
            response = requests.get(wheel_url, stream=True)
            response.raise_for_status()
            wheel_filename = f"{entry.get('name')}.whl"

            if not wheel_filename.endswith(".whl"):
                print(f"Downloaded file '{wheel_filename}' is not a valid wheel file. Skipping installation.")
                continue

            dir_name = Path(os.path.expanduser("~/.local/share/chaos/plugins"))
            dir_name.mkdir(parents=True, exist_ok=True)

            if wheel_filename in os.listdir(dir_name):
                print(f"Wheel '{wheel_filename}' is already installed. Skipping installation.")
                continue

            if ".." in wheel_filename or "/" in wheel_filename or "\\" in wheel_filename:
                print(f"Invalid wheel filename '{wheel_filename}'. Skipping installation.")
                continue

            with open(wheel_filename, "wb") as wheel_file:
                for chunk in response.iter_content(chunk_size=8192):
                    wheel_file.write(chunk)

            shutil.move(wheel_filename, dir_name / wheel_filename)
            from chaos.lib.plugDiscovery import get_plugins
            get_plugins(update_cache=True)

            print(f"Successfully installed wheel '{wheel_filename}' from entry '{entry}'.")

        except requests.RequestException as e:
            raise RuntimeError(f"Error downloading wheel from {wheel_url}: {e}")

def list_styx_entries(entries: list[str] | None) -> str:
    """Lists the available Styx registry entries."""
    registry_text = get_styx_registry()
    if registry_text is None:
        raise RuntimeError("Could not fetch Styx registry data.")

    if not entries:
        registry_data = OmegaConf.create(registry_text)
        registry_data = cast(DictConfig, registry_data)

        if 'styx' not in registry_data:
            return "Invalid registry format: 'styx' key not found."

        styx_entries = registry_data.styx
        keys = list(styx_entries.keys())
        full_list = ""
        for entry_name in keys:
            entry_data = styx_entries.get(entry_name, {})
            description = entry_data.get('about', 'No description available.')
            entry_string = f"""{entry_name}:
        description: {description}"""
            full_list += entry_string + "\n\n"

        return full_list.strip()

    parsed_entries = parse_styx_registry(registry_text, entries)
    full_list = ""
    for entry in parsed_entries:
        description = entry.get('about', 'No description available.')
        entry_string = f"""{entry.get('name')}:
    description: {description}"""
        full_list += entry_string + "\n\n"

    return full_list.strip()

def uninstall_styx_entries(entries: list[str]):
    """Uninstalls the given Styx registry entries."""
    parsed_entries = parse_styx_registry(get_styx_registry(), entries)
    for entry in parsed_entries:
        wheel_filename = f"{entry.get('name')}.whl"
        wheel_path = os.path.expanduser(f"~/.local/share/chaos/plugins/{wheel_filename}")
        if not os.path.exists(wheel_path):
            print(f"Wheel '{wheel_filename}' is not installed. Skipping uninstallation.")
            continue

        try:
            os.remove(wheel_path)
            from chaos.lib.plugDiscovery import get_plugins
            get_plugins(update_cache=True)
            print(f"Successfully uninstalled wheel '{wheel_filename}' from entry '{entry}'.")

        except Exception as e:
            raise RuntimeError(f"Error uninstalling wheel '{wheel_filename}': {e}")
