from __future__ import annotations

import functools
import json
import os
import sys
from importlib import import_module
from importlib.metadata import entry_points
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from chaos.lib.roles.role import Role

"""
Module for discovering and loading Ch-aOS plugins.
"""

"This helps with CHAOS_DEV_PATH for plugin development"
pluginDevPath = os.getenv("CHAOS_DEV_PATH", None)
if pluginDevPath:
    absPath = os.path.abspath(pluginDevPath)
    if os.path.exists(absPath):
        wheel_files = list(Path(absPath).glob("*.whl"))
        for whl in wheel_files:
            try:
                whl_path = str(whl.resolve())
                if whl_path not in sys.path:
                    sys.path.insert(0, whl_path)
            except Exception as e:
                print(
                    f"Warning: Could not load plugin wheel '{whl}': {e}",
                    file=sys.stderr,
                )
    else:
        print(
            f"Warning: Ch-aos plugin path '{absPath}' does not exist.", file=sys.stderr
        )


@functools.lru_cache(maxsize=None)
def get_plugins(
    update_cache: bool = False,
) -> tuple[
    dict[str, str],
    dict[str, str],
    dict[str, str],
    dict[str, str],
    dict[str, str],
    dict[str, str],
    dict[str, str],
    dict[str, str],
]:
    """
    Discover and load Ch-aOS plugins from specified directories and cache the results.

    Helps with performance through caching discovered plugins.

    Current Plugin Capabilities:
    Roles: Define new chaos roles for applying and managing an OS.
    Aliases: Define new aliases for existing roles.
    Keys: Define new keys for existing roles, allowing for better `chaos init chobolo`.
    Explanations: Define explanations for existing roles, enhancing user understanding.
    """
    plugin_dirs = [
        Path(
            os.getenv(
                "CHAOS_PLUGIN_DIR",
                Path.home() / ".local" / "share" / "chaos" / "plugins",
            )
        ),
        Path("/usr/share/chaos/plugins"),
    ]

    for plugin_dir in plugin_dirs:
        if not plugin_dir.exists():
            continue

        dir_path = str(plugin_dir.resolve())

        if dir_path not in sys.path:
            sys.path.insert(0, dir_path)

    CACHE_DIR = os.getenv("CHAOS_CACHE_DIR", Path.home() / ".cache" / "chaos")
    CACHE_FILE = Path(CACHE_DIR) / "plugins.json"
    cache_exists = CACHE_FILE.exists()

    if not update_cache and cache_exists:
        with open(CACHE_FILE, "r") as f:
            try:
                cache_data: dict[str, dict[str, str]] = json.load(f)
                if (
                    "roles" in cache_data
                    and "aliases" in cache_data
                    and "explanations" in cache_data
                    and "keys" in cache_data
                    and "providers" in cache_data
                    and "boats" in cache_data
                    and "limanis" in cache_data
                    and "isles" in cache_data
                ):
                    return (
                        cache_data["roles"],
                        cache_data["aliases"],
                        cache_data["explanations"],
                        cache_data["keys"],
                        cache_data["providers"],
                        cache_data["boats"],
                        cache_data["limanis"],
                        cache_data["isles"],
                    )
                else:
                    print(
                        "Warning: Invalid or outdated cache file format. Re-discovering plugins.",
                        file=sys.stderr,
                    )
            except json.JSONDecodeError:
                print(
                    "Warning: Could not read cache file. Re-discovering plugins.",
                    file=sys.stderr,
                )

    discovered_roles = {}
    discovered_aliases = {}
    discovered_explanations = {}
    discovered_keys = {}
    discovered_providers = {}
    discovered_boats = {}
    discovered_limanis = {}
    discovered_isles = {}
    eps = entry_points()

    role_eps = eps.select(group="chaos.roles")
    for ep in role_eps:
        discovered_roles[ep.name] = ep.value

    alias_eps = eps.select(group="chaos.aliases")
    for ep in alias_eps:
        discovered_aliases[ep.name] = ep.value

    exp_eps = eps.select(group="chaos.explain")
    for ep in exp_eps:
        discovered_explanations[ep.name] = ep.value

    keys_eps = eps.select(group="chaos.keys")
    for ep in keys_eps:
        discovered_keys[ep.name] = ep.value

    provider_eps = eps.select(group="chaos.providers")
    for ep in provider_eps:
        discovered_providers[ep.name] = ep.value

    for ep in eps.select(group="chaos.boats"):
        discovered_boats[ep.name] = ep.value

    for ep in eps.select(group="chaos.limanis"):
        discovered_limanis[ep.name] = ep.value

    for ep in eps.select(group="chaos.isles"):
        discovered_isles[ep.name] = ep.value

    try:
        Path(CACHE_DIR).mkdir(parents=True, exist_ok=True)
        with open(CACHE_FILE, "w") as f:
            json.dump(
                {
                    "roles": discovered_roles,
                    "aliases": discovered_aliases,
                    "explanations": discovered_explanations,
                    "keys": discovered_keys,
                    "providers": discovered_providers,
                    "boats": discovered_boats,
                    "limanis": discovered_limanis,
                    "isles": discovered_isles,
                },
                f,
                indent=4,
            )
        if update_cache or not cache_exists:
            print(f"Plugin cache saved to {CACHE_FILE}", file=sys.stderr)
    except OSError as e:
        print(
            f"Error: Could not write to cache file {CACHE_FILE}: {e}", file=sys.stderr
        )

    return (
        discovered_roles,
        discovered_aliases,
        discovered_explanations,
        discovered_keys,
        discovered_providers,
        discovered_boats,
        discovered_limanis,
        discovered_isles,
    )


def load_roles(
    roles_spec: dict[str, str], requested_names: list[str] | None = None
) -> dict[str, type[Role]]:
    """
    Load role functions based on their specifications.
    If requested_names is provided, only roles in that list will be loaded.
    """
    requested_names = requested_names or []
    loaded_roles: dict[str, type[Role]] = {}
    for name, spec in roles_spec.items():
        if requested_names is not None and name not in requested_names:
            continue
        try:
            module_name, func_name = spec.split(":", 1)
            module = import_module(module_name)
            loaded_roles[name] = getattr(module, func_name)
        except (ImportError, AttributeError, ValueError) as e:
            print(
                f"Warning: Could not load role '{name}' from spec '{spec}': {e}",
                file=sys.stderr,
            )
    return loaded_roles


def loadList(spec: str) -> list[str] | None:
    """Load a key based on its specification."""
    try:
        moduleName, obj = spec.split(":", 1)
        module = import_module(moduleName)
        return getattr(module, obj)
    except (ImportError, AttributeError, ValueError) as e:
        print(f"ERROR: Could not load key from spec '{spec}': {e}")
        return None
