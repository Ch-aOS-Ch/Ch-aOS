from typing import cast
from omegaconf import DictConfig, OmegaConf
from rich.console import Console
from chaos.lib.secret_backends.utils import flatten, _generic_handle_add, _generic_handle_rem, is_valid_age_key

console = Console()

"""
AGE specific handlers for add/rem/list
"""

def listAge(sops_file_override):
    try:
        sops_config = OmegaConf.load(sops_file_override)
        sops_config = cast(DictConfig, sops_config)
        creation_rules = sops_config.get('creation_rules')
        if not creation_rules:
            console.print("[bold yellow]Warning:[/] No 'creation_rules' found in the sops config. Nothing to do.")
            return

        all_age_keys_in_config = set()
        for rule in creation_rules:
            for key_group in rule.get('key_groups', []):
                if 'age' in key_group and key_group.age is not None:
                    all_age_keys_in_config.update(flatten(key_group.age))

        if not all_age_keys_in_config:
            console.print(f"[cyan]INFO:[/] No keys to be shown.")

        return all_age_keys_in_config

    except Exception as e:
        raise RuntimeError(f"Failed to update sops config file: {e}") from e

def handleAgeAdd(args, sops_file_override, keys):
    valids = set()
    for key in keys:
        clean_key = key.strip()
        if not is_valid_age_key(clean_key):
            console.print(f"[bold red]ERROR:[/] Invalid age key: {key}. Skipping.")
            console.print("[cyan]INFO:[/] To get your age public key:")
            console.print("[cyan]INFO:[/]   - From a native age private key file (e.g., ~/.config/chaos/keys.txt): [italic]age-keygen -y ~/.config/chaos/keys.txt[/]")
            console.print("[cyan]INFO:[/]   - From an SSH public key (e.g., ~/.ssh/id_rsa.pub, requires ssh-to-age): [italic]ssh-to-age -i ~/.ssh/id_rsa.pub[/]")
            continue
        valids.add(clean_key)

    _generic_handle_add('age', args, sops_file_override, valids)

def handleAgeRem(args, sops_file_override, keys):
    try:
        config_data = OmegaConf.load(sops_file_override)
        config_data = cast(DictConfig, config_data)
        creation_rules = config_data.get('creation_rules', [])
        if not creation_rules:
            console.print("[bold yellow]Warning:[/] No 'creation_rules' found in the sops config. Nothing to do.")
            return

        all_age_keys_in_config = set()
        for rule in creation_rules:
            for key_group in rule.get('key_groups', []):
                if 'age' in key_group and key_group.age is not None:
                    all_age_keys_in_config.update(flatten(key_group.age))

        keys_to_remove = set()
        for key_to_check in keys:
            clean_key = key_to_check.strip()

            if clean_key in all_age_keys_in_config:
                keys_to_remove.add(clean_key)
            else:
                console.print(f"[cyan]INFO:[/] Key: {key_to_check} not found in sops config. Skipping.")

        _generic_handle_rem('age', args, sops_file_override, keys_to_remove)

    except Exception as e:
        raise RuntimeError(f"Failed to update sops config file: {e}") from e
