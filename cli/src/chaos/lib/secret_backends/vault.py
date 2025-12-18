import sys
from omegaconf import OmegaConf
from rich.console import Console
from chaos.lib.secret_backends.utils import flatten, _generic_handle_add, _generic_handle_rem

console = Console()

def is_valid_vault_key(key):
    import hvac
    import requests.exceptions
    try:
        client = hvac.Client(url=key)
        seal_status = client.sys.read_seal_status()
        if not seal_status:
            return False, f"Vault URI '{key}' did not return a valid seal status or Vault server is unreachable."
        if 'sealed' in seal_status['data']:
            return True, f"Valid vault URI. Server status: {seal_status['data']['sealed']}."
        else:
            return False, f"Vault URI '{key}' is a reachable endpoint, but status check failed or returned unexpected data."
    except requests.exceptions.MissingSchema:
        return False, f"Vault URI '{key}' is an invalid URL format. Missing schema (e.g., 'https://')."
    except requests.exceptions.ConnectionError:
        return False, f"Vault URI '{key}' is a valid URL format but unreachable. Check network connectivity or if the Vault server is running."
    except Exception as e:
        return False, f"An unexpected error occurred while validating Vault URI '{key}': {e}"

def listVault(sops_file_override):
    try:
        sops_config = OmegaConf.load(sops_file_override)
        creation_rules = sops_config.get('creation_rules')
        if not creation_rules:
            console.print("[bold yellow]Warning:[/] No 'creation_rules' found in the sops config. Nothing to do.")
            return

        all_vault_keys_in_config = set()
        for rule in creation_rules:
            for key_group in rule.get('key_groups', []):
                if 'vault' in key_group and key_group.vault is not None:
                    all_vault_keys_in_config.update(flatten(key_group.vault))

        if not all_vault_keys_in_config:
            console.print(f"[cyan]INFO:[/] No keys to be shown.")

        return all_vault_keys_in_config

    except Exception as e:
        console.print(f"[bold red]ERROR:[/] Failed to update sops config file: {e}")
        sys.exit(1)

def handleVaultAdd(args, sops_file_override, keys):
    valids = set()
    for key in keys:
        clean_key = key.strip()
        is_valid, message = is_valid_vault_key(clean_key)
        if is_valid:
            console.print(f"[green]INFO:[/] {message}")
            valids.add(clean_key)
        else:
            console.print(f"[bold red]ERROR:[/] {message} Skipping key '{key}'.")
            continue
    
    _generic_handle_add('vault', args, sops_file_override, valids)

def handleVaultRem(args, sops_file_override, keys):
    try:
        config_data = OmegaConf.load(sops_file_override)
        creation_rules = config_data.get('creation_rules', [])
        if not creation_rules:
            console.print("[bold yellow]Warning:[/] No 'creation_rules' found in the sops config. Nothing to do.")
            return

        all_vault_keys_in_config = set()
        for rule in creation_rules:
            for key_group in rule.get('key_groups', []):
                if 'vault' in key_group and key_group.vault is not None:
                    all_vault_keys_in_config.update(flatten(key_group.vault))

        keys_to_remove = set()
        for key_to_check in keys:
            clean_key = key_to_check.strip()

            if clean_key in all_vault_keys_in_config:
                keys_to_remove.add(clean_key)
            else:
                console.print(f"[cyan]INFO:[/] Key: {key_to_check} not found in sops config. Skipping.")

        _generic_handle_rem('vault', args, sops_file_override, keys_to_remove)

    except Exception as e:
        console.print(f"[bold red]ERROR:[/] Failed to update sops config file: {e}")
        sys.exit(1)
