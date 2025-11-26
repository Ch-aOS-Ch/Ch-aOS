import os
import json
import sys
from importlib.metadata import entry_points
from importlib import import_module
from pathlib import Path
import site
import glob

pluginDevPath = os.getenv('CHAOS_DEV_PATH', None)
if pluginDevPath:
    absPath = os.path.abspath(pluginDevPath)
    if os.path.exists(absPath):
        sys.path.insert(0, pluginDevPath)
    else:
        print(f"Warning: Ch-aos plugin path '{absPath}' does not exist.", file=sys.stderr)

def get_plugins(update_cache=False):
    plugin_dirs = [
        Path.home() / ".local/share/chaos/plugins",
        Path("/usr/share/chaos/plugins")
    ]

    for plugin_dir in plugin_dirs:
        if not plugin_dir.exists():
            continue

        wheel_files = list(plugin_dir.glob("*.whl"))
        for whl in wheel_files:
            try:
                whl_path = str(whl.resolve())

                if whl_path not in sys.path:
                    sys.path.insert(0, whl_path) 

            except Exception as e:
                print(f"Warning: Could not load plugin wheel '{whl}': {e}", file=sys.stderr)

    CACHE_DIR = Path(os.path.expanduser("~/.cache/chaos"))
    CACHE_FILE = CACHE_DIR / "plugins.json"
    cache_exists = CACHE_FILE.exists()

    if not update_cache and cache_exists:
        with open(CACHE_FILE, 'r') as f:
            try:
                cache_data = json.load(f)
                if 'roles' in cache_data and 'aliases' in cache_data and 'explainations' in cache_data:
                    return cache_data['roles'], cache_data['aliases'], cache_data['explainations']
                else:
                    print("Warning: Invalid or outdated cache file format. Re-discovering plugins.", file=sys.stderr)
            except json.JSONDecodeError:
                print("Warning: Could not read cache file. Re-discovering plugins.", file=sys.stderr)

    discovered_roles = {}
    discovered_aliases = {}
    discovered_explainations = {}
    eps = entry_points()

    role_eps = eps.select(group="chaos.roles") if hasattr(eps, "select") else eps.get("chaos.roles", [])
    for ep in role_eps:
        discovered_roles[ep.name] = ep.value

    alias_eps = eps.select(group="chaos.aliases") if hasattr(eps, "select") else eps.get("chaos.aliases", [])
    for ep in alias_eps:
        discovered_aliases[ep.name] = ep.value

    exp_eps = eps.select(group="chaos.explain") if hasattr(eps, "select") else eps.get("chaos.explain", [])
    for ep in exp_eps:
        discovered_explainations[ep.name] = ep.value

    try:
        CACHE_DIR.mkdir(parents=True, exist_ok=True)
        with open(CACHE_FILE, 'w') as f:
            json.dump({'roles': discovered_roles, 'aliases': discovered_aliases, 'explainations': discovered_explainations}, f, indent=4)
        if update_cache or not cache_exists:
            print(f"Plugin cache saved to {CACHE_FILE}", file=sys.stderr)
    except OSError as e:
        print(f"Error: Could not write to cache file {CACHE_FILE}: {e}", file=sys.stderr)


    return discovered_roles, discovered_aliases, discovered_explainations

def load_roles(roles_spec):
    loaded_roles = {}
    for name, spec in roles_spec.items():
        try:
            module_name, func_name = spec.split(':', 1)
            module = import_module(module_name)
            loaded_roles[name] = getattr(module, func_name)
        except (ImportError, AttributeError, ValueError) as e:
            print(f"Warning: Could not load role '{name}' from spec '{spec}': {e}", file=sys.stderr)
    return loaded_roles
