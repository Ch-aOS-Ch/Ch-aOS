from rich.console import Console
from omegaconf import OmegaConf, ListConfig
from pathlib import Path
from rich.prompt import Confirm
from chaos.lib.checkers import is_vault_in_use, check_vault_auth
import os
import sys
import re
import math
import subprocess

console = Console()

def get_sops_files(sops_file_override, secrets_file_override, team):
    secretsFile = secrets_file_override
    sopsFile = sops_file_override

    CONFIG_DIR = os.path.expanduser("~/.config/chaos")
    CONFIG_FILE_PATH = os.path.join(CONFIG_DIR, "config.yml")

    global_config = {}
    if os.path.exists(CONFIG_FILE_PATH):
        global_config = OmegaConf.load(CONFIG_FILE_PATH) or OmegaConf.create()

    if team:
        if not '.' in team:
            Console().print("[bold red]ERROR:[/] Must set a company for your team. (company.team.group)")
            sys.exit(1)

        parts = team.split('.')
        company = parts[0]
        team = parts[1]

        if ".." in company or company.startswith("/"):
             console.print(f"[bold red]ERROR:[/] Invalid company name '{company}'.")
             sys.exit(1)

        if ".." in team or team.startswith("/"):
             console.print(f"[bold red]ERROR:[/] Invalid team name '{team}'.")
             sys.exit(1)

        teamPath = Path(os.path.expanduser(f'~/.local/share/chaos/teams/{company}/{team}'))

        if teamPath.exists():

            teamSops = teamPath / sops_file_override if sops_file_override else teamPath / "sops-config.yml"
            teamSec = teamPath / f'secrets/{secrets_file_override}' if secrets_file_override else teamPath / f"secrets/secrets.yml"

            if not teamSops.exists() or not teamSec.exists():
                Console().print(f"[bold red]ERROR:[/] Either secrets file doesn't exist or sops file doesn't exist.")
                sys.exit(1)
            sopsFile = teamSops if teamSops.exists() else sopsFile
            secretsFile = teamSec if teamSec.exists() else secretsFile

            if secrets_file_override and ('..' in secrets_file_override or secrets_file_override.startswith('/')):
                Console().print("[bold red]ERROR:[/]Team secrets file is invalid. Skipping.")
                sys.exit(1)
            if sops_file_override and ('..' in sops_file_override or sops_file_override.startswith('/')):
                Console().print("[bold red]ERROR:[/]Team sops file is invalid. Skipping.")
                sys.exit(1)
        else:
            console.print(f"[bold red]ERROR:[/] Team directory for '{team}' not found at {teamPath}.")
            sys.exit(1)

    if not secretsFile:
        secretsFile = global_config.get('secrets_file')
    if not sopsFile:
        sopsFile = global_config.get('sops_file')

    if not secretsFile or not sopsFile:
        ChOboloPath = global_config.get('chobolo_file', None)
        if ChOboloPath:
            try:
                ChObolo = OmegaConf.load(ChOboloPath)
                secrets_config = ChObolo.get('secrets', None)
                if secrets_config:
                    if not secretsFile:
                        secretsFile = secrets_config.get('sec_file')
                    if not sopsFile:
                        sopsFile = secrets_config.get('sec_sops')
            except Exception as e:
                print(f"WARNING: Could not load Chobolo fallback '{ChOboloPath}': {e}", file=sys.stderr)

    return secretsFile, sopsFile

def flatten(items):
    for i in items:
        if isinstance(i, (list, ListConfig)):
            yield from flatten(i)
        else:
            yield i

def is_valid_fp(fp):
    clean_fingerprint = fp.replace(" ", "").replace("\n", "")
    if re.fullmatch(r"^[0-9A-Fa-f]{40}$", clean_fingerprint):
        return True
    else:
        return False

def pgp_exists(fp):
    try:
        subprocess.run(
            ['gpg', '--list-keys', fp],
            check=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )
        return True
    except subprocess.CalledProcessError:
        return False

def is_valid_age_key(key):
    return re.fullmatch(r"age1[a-z0-9]{58}", key)

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

def listPgp(sops_file_override):
    try:
        sops_config = OmegaConf.load(sops_file_override)
        creation_rules = sops_config.get('creation_rules')
        if not creation_rules:
            console.print("[bold yellow]Warning:[/] No 'creation_rules' found in the sops config. Nothing to do.")
            return

        all_pgp_keys_in_config = set()
        for rule in creation_rules:
            for key_group in rule.get('key_groups', []):
                if 'pgp' in key_group and key_group.pgp is not None:
                    all_pgp_keys_in_config.update(flatten(key_group.pgp))

        if not all_pgp_keys_in_config:
            console.print(f"[cyan]INFO:[/] No keys to be shown.")

        return all_pgp_keys_in_config

    except Exception as e:
        console.print(f"[bold red]ERROR:[/] Failed to update sops config file: {e}")
        sys.exit(1)

def listAge(sops_file_override):
    try:
        sops_config = OmegaConf.load(sops_file_override)
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
        console.print(f"[bold red]ERROR:[/] Failed to update sops config file: {e}")
        sys.exit(1)

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

def handlePgpAdd(args, sops_file_override, keys):
    server = args.pgp_server
    valids = set()
    for key in keys:
        clean_key = key.replace(" ", "")
        if len(clean_key) < 40:
            console.print(f"[bold yellow]WARNING:[/] Unsafe PGP key fingerprint: {key}. Skipping.")
            console.print("[cyan]INFO:[/] To list your GPG keys, run: [italic]gpg --list-secret-keys --keyid-format LONG[/]")
            continue

        if not is_valid_fp(clean_key):
            console.print(f"[bold red]ERROR:[/] Invalid PGP fingerprint: {key}. Skipping.")
            console.print("[cyan]INFO:[/] To list your GPG keys, run: [italic]gpg --list-secret-keys --keyid-format LONG[/]")
            continue

        if not pgp_exists(clean_key):
            console.print(f"[bold yellow]WARNING:[/] PGP fingerprint {key} does not exist locally.")
            if not server:
                console.print(f"[bold red]ERROR:[/] PGP fingerprint {key} does not exist locally and no server was passed. Skipping")
                console.print("[cyan]INFO:[/] To list your GPG keys, run: [italic]gpg --list-secret-keys --keyid-format LONG[/]")
                continue
            try:
                subprocess.run(['gpg', '--keyserver', server, '--recv-keys', clean_key], check=True)
                console.print(f"[green]Fingerprint {key} was successfully imported from {server}")
            except subprocess.SubprocessError as e:
                console.print(f"[bold red]ERROR:[/] Could not import {key} from {server}: {e}.\nSkipping.")
                continue
        valids.add(clean_key)

    if not valids:
        console.print("No valid keys. Returning.")
        return

    try:
        create = args.create
        config_data = OmegaConf.load(sops_file_override)
        creation_rules = config_data.get('creation_rules', [])
        if not creation_rules:
            console.print(f"[bold red]ERROR:[/] No 'creation_rules' found in {sops_file_override}. Cannot add keys.")
            sys.exit(1)

        rule_index = getattr(args, 'index', None)
        rules_to_process = creation_rules
        if rule_index is not None:
            if not (0 <= rule_index < len(creation_rules)):
                console.print(f"[bold red]ERROR:[/] Invalid rule index {rule_index}. Must be between 0 and {len(creation_rules) - 1}.")
                sys.exit(1)
            rules_to_process = [creation_rules[rule_index]]

        if not create:
            total_added_keys = set()
            for rule in rules_to_process:
                for key_group in rule.get('key_groups', []):
                    if 'pgp' in key_group and key_group.pgp is not None:
                        existing_keys = list(flatten(key_group.pgp))

                        keys_to_write = list(existing_keys)
                        current_keys_set = set(keys_to_write)
                        for key_to_add in valids:
                            if key_to_add not in current_keys_set:
                                keys_to_write.append(key_to_add)
                                total_added_keys.add(key_to_add)

                        key_group.pgp = keys_to_write

            if not total_added_keys:
                console.print("[yellow]All provided keys are already in the relevant sops config 'pgp' sections, or no 'pgp' sections were found. No changes made.[/]")
                return

            OmegaConf.save(config_data, sops_file_override)
            console.print(f"[bold green]Successfully updated sops config![/] New keys added: {list(total_added_keys)}")
        else:
            for rule in rules_to_process:
                new_group = OmegaConf.create({'pgp': list(valids)})
                if 'key_groups' in rule and rule.key_groups is not None:
                    rule.key_groups.append(new_group)
                else:
                    rule.key_groups = [new_group]

            OmegaConf.save(config_data, sops_file_override)
            console.print(f"[bold green]Successfully updated sops config![/] New PGP key group created with keys: {list(valids)}")


    except Exception as e:
        console.print(f"[bold red]ERROR:[/] Failed to load or save sops config file {sops_file_override}: {e}")
        sys.exit(1)

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

    if not valids:
        console.print("No valid keys. Returning.")
        return

    try:
        create = args.create
        config_data = OmegaConf.load(sops_file_override)
        creation_rules = config_data.get('creation_rules', [])
        if not creation_rules:
            console.print(f"[bold red]ERROR:[/] No 'creation_rules' found in {sops_file_override}. Cannot add keys.")
            sys.exit(1)

        rule_index = getattr(args, 'index', None)

        rules_to_process = creation_rules
        if rule_index is not None:
            if not (0 <= rule_index < len(creation_rules)):
                console.print(f"[bold red]ERROR:[/] Invalid rule index {rule_index}. Must be between 0 and {len(creation_rules) - 1}.")
                sys.exit(1)
            rules_to_process = [creation_rules[rule_index]]

        if not create:
            total_added_keys = set()
            for rule in rules_to_process:
                for key_group in rule.get('key_groups', []):
                    if 'age' in key_group and key_group.age is not None:
                        existing_keys = list(flatten(key_group.age))

                        keys_to_write = list(existing_keys)
                        current_keys_set = set(keys_to_write)
                        for key_to_add in valids:
                            if key_to_add not in current_keys_set:
                                keys_to_write.append(key_to_add)
                                total_added_keys.add(key_to_add)

                        key_group.age = keys_to_write

            if not total_added_keys:
                console.print("[yellow]All provided keys are already in the relevant sops config 'age' sections, or no 'age' sections were found. No changes made.[/]")
                return

            OmegaConf.save(config_data, sops_file_override)
            console.print(f"[bold green]Successfully updated sops config![/] New keys added: {list(total_added_keys)}")
        else:
            for rule in rules_to_process:
                new_group = OmegaConf.create({'age': list(valids)})
                if 'key_groups' in rule and rule.key_groups is not None:
                    rule.key_groups.append(new_group)
                else:
                    rule.key_groups = [new_group]

            OmegaConf.save(config_data, sops_file_override)
            console.print(f"[bold green]Successfully updated sops config![/] New age key group created with keys: {list(valids)}")

    except Exception as e:
        console.print(f"[bold red]ERROR:[/] Failed to load or save sops config file {sops_file_override}: {e}")
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

    if not valids:
        console.print("No valid keys. Returning.")
        return
    try:
        create = args.create
        config_data = OmegaConf.load(sops_file_override)
        creation_rules = config_data.get('creation_rules', [])
        if not creation_rules:
            console.print(f"[bold red]ERROR:[/] No 'creation_rules' found in {sops_file_override}. Cannot add keys.")
            sys.exit(1)

        rule_index = getattr(args, 'index', None)

        rules_to_process = creation_rules
        if rule_index is not None:
            if not (0 <= rule_index < len(creation_rules)):
                console.print(f"[bold red]ERROR:[/] Invalid rule index {rule_index}. Must be between 0 and {len(creation_rules) - 1}.")
                sys.exit(1)
            rules_to_process = [creation_rules[rule_index]]

        if not create:
            total_added_keys = set()
            for rule in rules_to_process:
                for key_group in rule.get('key_groups', []):
                    if 'vault' in key_group and key_group.vault is not None:
                        existing_keys = list(flatten(key_group.vault))

                        keys_to_write = list(existing_keys)
                        current_keys_set = set(keys_to_write)
                        for key_to_add in valids:
                            if key_to_add not in current_keys_set:
                                keys_to_write.append(key_to_add)
                                total_added_keys.add(key_to_add)

                        key_group.vault = keys_to_write

            if not total_added_keys:
                console.print("[yellow]All provided keys are already in the relevant sops config 'vault' sections, or no 'vault' sections were found. No changes made.[/]")
                return

            OmegaConf.save(config_data, sops_file_override)
            console.print(f"[bold green]Successfully updated sops config![/] New keys added: {list(total_added_keys)}")
        else:
            for rule in rules_to_process:
                new_group = OmegaConf.create({'vault': list(valids)})
                if 'key_groups' in rule and rule.key_groups is not None:
                    rule.key_groups.append(new_group)
                else:
                    rule.key_groups = [new_group]

            OmegaConf.save(config_data, sops_file_override)
            console.print(f"[bold green]Successfully updated sops config![/] New Vault key group created with keys: {list(valids)}")

    except Exception as e:
        console.print(f"[bold red]ERROR:[/] Failed to load or save sops config file {sops_file_override}: {e}")
        sys.exit(1)

def handlePgpRem(args, sops_file_override, keys):
    rule_index = getattr(args, 'index', None)
    ikwid = getattr(args, 'i_know_what_im_doing', False)
    try:
        config_data = OmegaConf.load(sops_file_override)
        creation_rules = config_data.get('creation_rules', [])
        if not creation_rules:
            console.print("[bold yellow]Warning:[/] No 'creation_rules' found in the sops config. Nothing to do.")
            return

        all_pgp_keys_in_config = set()
        for rule in creation_rules:
            for key_group in rule.get('key_groups', []):
                if 'pgp' in key_group and key_group.pgp is not None:
                    all_pgp_keys_in_config.update(flatten(key_group.pgp))

        keys_to_remove = set()
        for key_to_check in keys:
            clean_key = key_to_check.replace(" ", "")
            if not is_valid_fp(clean_key):
                console.print(f"[bold red]ERROR:[/] Invalid PGP fingerprint: {key_to_check}. Skipping.")
                continue

            if clean_key in all_pgp_keys_in_config:
                keys_to_remove.add(clean_key)
            else:
                console.print(f"[cyan]INFO:[/] Fingerprint: {key_to_check} not found in sops config. Skipping.")

        if not keys_to_remove:
            console.print("No keys to remove. Exiting.")
            return

        if not ikwid:
            console.print("Keys to remove:")
            for key in keys_to_remove:
                console.print(f"  {key}")

        confirm = True if ikwid else Confirm.ask("Are you sure you want to remove these keys?", default=False)
        if not confirm:
            console.print("Aborting.")
            return

        rules_to_process = creation_rules
        if rule_index is not None:
            if not (0 <= rule_index < len(creation_rules)):
                console.print(f"[bold red]ERROR:[/] Invalid rule index {rule_index}. Must be between 0 and {len(creation_rules) - 1}.")
                sys.exit(1)
            rules_to_process = [creation_rules[rule_index]]

        for rule in rules_to_process:
            if rule.get('key_groups'):
                for i in range(len(rule.key_groups) - 1, -1, -1):
                    key_group = rule.key_groups[i]
                    if 'pgp' in key_group and key_group.pgp is not None:
                        updated_keys = [k for k in flatten(key_group.pgp) if k not in keys_to_remove]
                        if updated_keys:
                            key_group.pgp = updated_keys
                        else:
                            del key_group.pgp

                    if not key_group:
                        del rule.key_groups[i]

        OmegaConf.save(config_data, sops_file_override)
        console.print(f"[bold green]Successfully updated sops config![/] Keys removed: {list(keys_to_remove)}")

    except Exception as e:
        console.print(f"[bold red]ERROR:[/] Failed to update sops config file: {e}")
        sys.exit(1)

def handleAgeRem(args, sops_file_override, keys):
    rule_index = getattr(args, 'index', None)
    ikwid = getattr(args, 'i_know_what_im_doing', False)
    try:
        config_data = OmegaConf.load(sops_file_override)
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

        if not keys_to_remove:
            console.print("No keys to remove. Exiting.")
            return

        if not ikwid:
            console.print("Keys to remove:")
            for key in keys_to_remove:
                console.print(f"  {key}")

        confirm = True if ikwid else Confirm.ask("Are you sure you want to remove these keys?", default=False)
        if not confirm:
            console.print("Aborting.")
            return

        rules_to_process = creation_rules
        if rule_index is not None:
            if not (0 <= rule_index < len(creation_rules)):
                console.print(f"[bold red]ERROR:[/] Invalid rule index {rule_index}. Must be between 0 and {len(creation_rules) - 1}.")
                sys.exit(1)
            rules_to_process = [creation_rules[rule_index]]

        for rule in rules_to_process:
            if rule.get('key_groups'):
                for i in range(len(rule.key_groups) - 1, -1, -1):
                    key_group = rule.key_groups[i]
                    if 'age' in key_group and key_group.age is not None:
                        updated_keys = [k for k in flatten(key_group.age) if k not in keys_to_remove]
                        if updated_keys:
                            key_group.age = updated_keys
                        else:
                            del key_group.age

                    if not key_group:
                        del rule.key_groups[i]

        OmegaConf.save(config_data, sops_file_override)
        console.print(f"[bold green]Successfully updated sops config![/] Keys removed: {list(keys_to_remove)}")

    except Exception as e:
        console.print(f"[bold red]ERROR:[/] Failed to update sops config file: {e}")
        sys.exit(1)

def handleVaultRem(args, sops_file_override, keys):
    rule_index = getattr(args, 'index', None)
    ikwid = getattr(args, 'i_know_what_im_doing', False)
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

        if not keys_to_remove:
            console.print("No keys to remove. Exiting.")
            return

        if not ikwid:
            console.print("Keys to remove:")
            for key in keys_to_remove:
                console.print(f"  {key}")

        confirm = True if ikwid else Confirm.ask("Are you sure you want to remove these keys?", default=False)
        if not confirm:
            console.print("Aborting.")
            return

        rules_to_process = creation_rules
        if rule_index is not None:
            if not (0 <= rule_index < len(creation_rules)):
                console.print(f"[bold red]ERROR:[/] Invalid rule index {rule_index}. Must be between 0 and {len(creation_rules) - 1}.")
                sys.exit(1)
            rules_to_process = [creation_rules[rule_index]]

        for rule in rules_to_process:
            if rule.get('key_groups'):
                for i in range(len(rule.key_groups) - 1, -1, -1):
                    key_group = rule.key_groups[i]
                    if 'vault' in key_group and key_group.vault is not None:
                        updated_keys = [k for k in flatten(key_group.vault) if k not in keys_to_remove]
                        if updated_keys:
                            key_group.vault = updated_keys
                        else:
                            del key_group.vault

                    if not key_group:
                        del rule.key_groups[i]

        OmegaConf.save(config_data, sops_file_override)
        console.print(f"[bold green]Successfully updated sops config![/] Keys removed: {list(keys_to_remove)}")

    except Exception as e:
        console.print(f"[bold red]ERROR:[/] Failed to update sops config file: {e}")
        sys.exit(1)

def handleUpdateAllSecrets(args):
    console.print("\n[bold cyan]Starting key update for all secret files...[/]")

    sops_file_override = getattr(args, 'sops_file_override', None)
    secrets_file_override = getattr(args, 'secrets_file_override', None)
    team = getattr(args, 'team', None)

    main_secrets_file, sops_file_path = get_sops_files(sops_file_override, secrets_file_override, team)

    if is_vault_in_use(sops_file_path):
        is_authed, message = check_vault_auth()
        if not is_authed:
            console.print(message)
            sys.exit(1)

    if not sops_file_path:
        console.print("[bold yellow]Warning:[/] No sops config file found for main secrets. Skipping main secrets file update.")
    elif main_secrets_file and Path(main_secrets_file).exists():
        try:
            data = OmegaConf.load(main_secrets_file)
            if "sops" in data:
                console.print(f"Updating keys for main secrets file: [cyan]{main_secrets_file}[/]")
                result = subprocess.run(
                    ['sops', '--config', sops_file_path, 'updatekeys', main_secrets_file],
                    check=True, input="y", text=True, capture_output=True
                )
                console.print("[green]Keys updated successfully.[/green]")
        except subprocess.CalledProcessError as e:
            console.print(f'[bold red]ERROR:[/] Failed to update keys for {main_secrets_file}: {e.stderr}')
        except Exception as e:
            console.print(f'[bold red]ERROR:[/] Could not process file {main_secrets_file}: {e}')
    else:
        console.print("[dim]Main secrets file not found or not configured. Skipping.[/dim]")

    console.print("\n[bold cyan]Updating ramble files...[/]")
    from chaos.lib.ramble import handleUpdateEncryptRamble
    handleUpdateEncryptRamble(args)

def handleRotateAdd(args):
    sops_file_override = getattr(args, 'sops_file_override', None)
    secrets_file_override = getattr(args, 'secrets_file_override', None)
    team = getattr(args, 'team', None)

    _, sops_file_override = get_sops_files(sops_file_override, secrets_file_override, team)

    keys = args.keys

    if not sops_file_override:
        console.print("[bold red]ERROR:[/] No sops config file found. Exiting")
        sys.exit(1)

    match args.type:
        case 'pgp': handlePgpAdd(args, sops_file_override, keys)
        case 'age': handleAgeAdd(args, sops_file_override, keys)
        case 'vault': handleVaultAdd(args, sops_file_override, keys)
        case _:
            console.print("No available type passed. Exiting.")
            return
    ikwid = args.i_know_what_im_doing

    confirm = True if ikwid else Confirm.ask("Do you wish to update all encrypted files with the new keys?", default=True)
    if confirm:
        handleUpdateAllSecrets(args)

def handleRotateRemove(args):
    sops_file_override = getattr(args, 'sops_file_override', None)
    secrets_file_override = getattr(args, 'secrets_file_override', None)
    team = getattr(args, 'team', None)

    _, sops_file_override = get_sops_files(sops_file_override, secrets_file_override, team)

    keys = args.keys

    if not sops_file_override:
        console.print("[bold red]ERROR:[/] No sops config file found. Exiting")
        sys.exit(1)

    ikwid = args.i_know_what_im_doing
    match args.type:
        case 'pgp': handlePgpRem(args, sops_file_override, keys)
        case 'age': handleAgeRem(args, sops_file_override, keys)
        case 'vault': handleVaultRem(args, sops_file_override, keys)
        case _:
            console.print("No available type passed. Exiting.")
            return
    confirm = True if ikwid else Confirm.ask("Do you wish to update all encrypted files with the new keys?", default=True)
    if confirm:
        handleUpdateAllSecrets(args)

def listFp(args):
    from rich.panel import Panel
    from itertools import zip_longest
    from rich.align import Align
    from rich.table import Table
    sops_file_override = getattr(args, 'sops_file_override', None)
    secrets_file_override = getattr(args, 'secrets_file_override', None)
    team = getattr(args, 'team', None)

    _, sops_file_override = get_sops_files(sops_file_override, secrets_file_override, team)

    if not sops_file_override:
        console.print("[bold red]ERROR:[/] No sops config file found. Exiting")
        sys.exit(1)

    match args.type:
        case 'pgp': results = listPgp(sops_file_override)
        case 'age': results = listAge(sops_file_override)
        case 'vault': results = listVault(sops_file_override)
        case _:
            console.print("No available type passed. Exiting.")
            return

    if results != None:
        items = sorted(results)
        num_items = len(results)
        max_rows = 4

        if num_items < 5:
            table = Table(show_lines=True, expand=False, show_header=False)
            table.add_column(justify="center")

            for item in items:
                table.add_row(f"[italic][cyan]{item}[/][/]")

            console.print(Align.center(Panel(Align.center(table), border_style="green", expand=False, title=f"[italic][green]Found {args.type} Keys:[/][/]")), justify="center")
        else:
            num_columns = math.ceil(num_items / max_rows)

            table = Table(
                show_lines=True,
                expand=False,
                show_header=False
            )

            for _ in range(num_columns):
                table.add_column(justify="center")

            chunks = [items[i:i + max_rows] for i in range(0, num_items, max_rows)]
            transposed_items = zip_longest(*chunks, fillvalue="")

            for row_data in transposed_items:
                styled_row = [f"[cyan][italic]{item}[/][/]" if item else "" for item in row_data]
                table.add_row(*styled_row)

            console.print(Align.center(Panel(Align.center(table), border_style="green", expand=False, title=f"[italic][green]Found {args.type} Keys:[/][/]")), justify="center")

def handleSetShamir(args):
    sops_file_override = getattr(args, 'sops_file_override', None)
    secrets_file_override = getattr(args, 'secrets_file_override', None)
    team = getattr(args, 'team', None)

    _, sops_file_override = get_sops_files(sops_file_override, secrets_file_override, team)

    if not sops_file_override:
        console.print("[bold red]ERROR:[/] No sops config file found. Exiting")
        sys.exit(1)

    if not os.path.exists(sops_file_override):
        console.print(f"[bold red]ERROR:[/] Sops config file does not exist at path: {sops_file_override}")
        sys.exit(1)

    threshold: int = args.share
    rule_index: int = args.index
    ikwid = getattr(args, 'i_know_what_im_doing', False)

    try:
        config_data = OmegaConf.load(sops_file_override)
        creation_rules = config_data.get('creation_rules')

        if not creation_rules:
            console.print(f"[bold red]ERROR:[/] No 'creation_rules' found in {sops_file_override}. Cannot set Shamir threshold.")
            sys.exit(1)

        if not (0 <= rule_index < len(creation_rules)):
            console.print(f"[bold red]ERROR:[/] Invalid rule index {rule_index}. Must be between 0 and {len(creation_rules) - 1}.")
            sys.exit(1)

        rule = creation_rules[rule_index]
        key_groups = rule.get('key_groups', [])
        num_key_groups = len(key_groups)

        if threshold <= 0:
            if rule.get('shamir_threshold') is not None:
                confirm = True if ikwid else Confirm.ask(f"Are you sure you want to remove the Shamir threshold from rule {rule_index}?", default=False)

                if confirm:
                    del rule['shamir_threshold']
                    OmegaConf.save(config_data, sops_file_override)
                    console.print(f"[bold green]Successfully removed Shamir threshold from rule {rule_index} in {sops_file_override}[/]")
                    confirm_update = True if ikwid else Confirm.ask("Do you wish to update all encrypted files with this change?", default=True)
                    if confirm_update:
                        handleUpdateAllSecrets(args)
                else:
                    console.print("Aborting.")
            else:
                console.print(f"No Shamir threshold to remove from rule {rule_index}.")

            return

        if num_key_groups < 2:
            console.print(f"[bold red]ERROR:[/] Shamir threshold requires at least 2 key groups for rule {rule_index}, but only {num_key_groups} is defined.")
            sys.exit(1)

        if not (1 <= threshold <= num_key_groups):
            console.print(f"[bold red]ERROR:[/] Shamir threshold ({threshold}) must be between 1 and the number of key groups ({num_key_groups}).")
            sys.exit(1)

        rule['shamir_threshold'] = threshold

        OmegaConf.save(config=config_data, f=sops_file_override)

        console.print(f"[bold green]Successfully set Shamir threshold to {threshold} for rule {rule_index} in {sops_file_override}[/]")

        confirm = True if ikwid else Confirm.ask("Do you wish to update all encrypted files with the new threshold?", default=True)
        if confirm:
            handleUpdateAllSecrets(args)

    except Exception as e:
        console.print(f"[bold red]ERROR:[/] Failed to update sops config file: {e}")
        sys.exit(1)

def handleSecEdit(args):
    team = args.team
    sops_file_override = args.sops_file_override
    secrets_file_override = args.secrets_file_override
    secretsFile, sopsFile = get_sops_files(sops_file_override, secrets_file_override, team)

    if is_vault_in_use(sopsFile):
        is_authed, message = check_vault_auth()
        if not is_authed:
            console.print(message)
            sys.exit(1)

    if not secretsFile or not sopsFile:
        print("ERROR: SOPS check requires both secrets file and sops config file paths.", file=sys.stderr)
        print("       Configure them using 'chaos set sec' and 'chaos set sops', or pass them with '-sf' and '-ss'.", file=sys.stderr)
        sys.exit(1)

    try:
        subprocess.run(['sops', '--config', sopsFile, secretsFile], check=True)
    except subprocess.CalledProcessError as e:
        if e.returncode == 200:
            print("File has not changed, exiting.")
            sys.exit(0)
        else:
            print(f"ERROR: SOPS editing failed with exit code {e.returncode}.", file=sys.stderr)
            sys.exit(1)
    except FileNotFoundError:
        print("ERROR: 'sops' command not found. Please ensure sops is installed and in your PATH.", file=sys.stderr)
        sys.exit(1)

def handleSecPrint(args):
    team = args.team
    sops_file_override = args.sops_file_override
    secrets_file_override = args.secrets_file_override
    secretsFile, sopsFile = get_sops_files(sops_file_override, secrets_file_override, team)

    if is_vault_in_use(sopsFile):
        is_authed, message = check_vault_auth()
        if not is_authed:
            console.print(message)
            sys.exit(1)

    if not secretsFile or not sopsFile:
        print("ERROR: SOPS check requires both secrets file and sops config file paths.", file=sys.stderr)
        print("       Configure them using 'chaos -sec' and 'chaos -sops', or pass them with '-sf' and '-ss'.", file=sys.stderr)
        sys.exit(1)

    try:
        subprocess.run(['sops', '--config', sopsFile, '--decrypt', secretsFile], check=True)
    except subprocess.CalledProcessError as e:
        print("ERROR: SOPS decryption failed.")
        print("Details:", e.stderr.decode() if e.stderr else "No output.")
        sys.exit(1)
    except FileNotFoundError:
        print("ERROR: 'sops' command not found. Please ensure sops is installed and in your PATH.", file=sys.stderr)
        sys.exit(1)

