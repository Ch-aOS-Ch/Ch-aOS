from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.align import Align
from itertools import zip_longest
from omegaconf import OmegaConf, ListConfig
from pathlib import Path
from rich.prompt import Confirm
import os
import sys
import re
import math
import subprocess

console = Console()

def _get_sops_files(sops_file_override, secrets_file_override):
    secretsFile = secrets_file_override
    sopsFile = sops_file_override

    CONFIG_DIR = os.path.expanduser("~/.config/chaos")
    CONFIG_FILE_PATH = os.path.join(CONFIG_DIR, "config.yml")

    global_config = {}
    if os.path.exists(CONFIG_FILE_PATH):
        global_config = OmegaConf.load(CONFIG_FILE_PATH) or OmegaConf.create()

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
        config_data = OmegaConf.load(sops_file_override)

        creation_rules = config_data.get('creation_rules', [])
        if not creation_rules:
            console.print(f"[bold red]ERROR:[/] No 'creation_rules' found in {sops_file_override}. Cannot add keys.")
            sys.exit(1)

        total_added_keys = set()
        for rule in creation_rules:
            for key_group in rule.get('key_groups', []):

                existing_keys = []
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
            console.print("[yellow]All provided keys are already in the sops config or no 'pgp' section was found to add them. No changes made.[/]")
            return

        OmegaConf.save(config_data, sops_file_override)
        console.print(f"[bold green]Successfully updated sops config![/] New keys added: {list(total_added_keys)}")

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
        config_data = OmegaConf.load(sops_file_override)
        creation_rules = config_data.get('creation_rules', [])
        if not creation_rules:
            console.print(f"[bold red]ERROR:[/] No 'creation_rules' found in {sops_file_override}. Cannot add keys.")
            sys.exit(1)

        total_added_keys = set()
        for rule in creation_rules:
            for key_group in rule.get('key_groups', []):
                existing_keys = []
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
            console.print("[yellow]All provided keys are already in the sops config. No changes made.[/]")
            return

        OmegaConf.save(config_data, sops_file_override)
        console.print(f"[bold green]Successfully updated sops config![/] New keys added: {list(total_added_keys)}")

    except Exception as e:
        console.print(f"[bold red]ERROR:[/] Failed to load or save sops config file {sops_file_override}: {e}")
        sys.exit(1)

def handlePgpRem(sops_file_override, keys, ikwid):
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

        for rule in creation_rules:
            for key_group in rule.get('key_groups', []):
                if 'pgp' in key_group and key_group.pgp is not None:
                    key_group.pgp = [k for k in flatten(key_group.pgp) if k not in keys_to_remove]

        OmegaConf.save(config_data, sops_file_override)
        console.print(f"[bold green]Successfully updated sops config![/] Keys removed: {list(keys_to_remove)}")

    except Exception as e:
        console.print(f"[bold red]ERROR:[/] Failed to update sops config file: {e}")
        sys.exit(1)

def handleAgeRem(sops_file_override, keys, ikwid):
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
            if not is_valid_age_key(clean_key):
                console.print(f"[bold red]ERROR:[/] Invalid age key: {key_to_check}. Skipping.")
                continue

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

        for rule in creation_rules:
            for key_group in rule.get('key_groups', []):
                if 'age' in key_group and key_group.age is not None:
                    key_group.age = [k for k in flatten(key_group.age) if k not in keys_to_remove]

        OmegaConf.save(config_data, sops_file_override)
        console.print(f"[bold green]Successfully updated sops config![/] Keys removed: {list(keys_to_remove)}")

    except Exception as e:
        console.print(f"[bold red]ERROR:[/] Failed to update sops config file: {e}")
        sys.exit(1)

def handleUpdateAllSecrets(args):
    console.print("\n[bold cyan]Starting key update for all secret files...[/]")

    sops_file_override = getattr(args, 'sops_file_override', None)
    secrets_file_override = getattr(args, 'secrets_file_override', None)

    main_secrets_file, sops_file_path = _get_sops_files(sops_file_override, secrets_file_override)

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
    GLOBAL_CONFIG_DIR = os.path.expanduser("~/.config/chaos")
    GLOBAL_CONFIG_FILE_PATH = os.path.join(GLOBAL_CONFIG_DIR, "config.yml")
    global_config = {}

    if os.path.exists(GLOBAL_CONFIG_FILE_PATH):
        global_config = OmegaConf.load(GLOBAL_CONFIG_FILE_PATH) or OmegaConf.create()

    sops_file_override = None
    if hasattr(args, 'sops_file_override') and args.sops_file_override:
        sops_file_override = args.sops_file_override
    else:
        sops_file_override = global_config.get('sops_file')

    keys = args.keys

    if not sops_file_override:
        console.print("[bold red]ERROR:[/] No sops config file found. Exiting")
        sys.exit(1)

    match args.type:
        case 'pgp': handlePgpAdd(args, sops_file_override, keys)
        case 'age': handleAgeAdd(args, sops_file_override, keys)
        case _:
            console.print("No available type passed. Exiting.")
            return
    ikwid = args.i_know_what_im_doing

    confirm = True if ikwid else Confirm.ask("Do you wish to update all encrypted files with the new keys?", default=True)
    if confirm:
        handleUpdateAllSecrets(args)

def handleRotateRemove(args):
    GLOBAL_CONFIG_DIR = os.path.expanduser("~/.config/chaos")
    GLOBAL_CONFIG_FILE_PATH = os.path.join(GLOBAL_CONFIG_DIR, "config.yml")
    global_config = {}

    if os.path.exists(GLOBAL_CONFIG_FILE_PATH):
        global_config = OmegaConf.load(GLOBAL_CONFIG_FILE_PATH) or OmegaConf.create()

    sops_file_override = None
    if hasattr(args, 'sops_file_override') and args.sops_file_override:
        sops_file_override = args.sops_file_override
    else:
        sops_file_override = global_config.get('sops_file')

    keys = args.keys

    if not sops_file_override:
        console.print("[bold red]ERROR:[/] No sops config file found. Exiting")
        sys.exit(1)

    ikwid = args.i_know_what_im_doing
    match args.type:
        case 'pgp': handlePgpRem(sops_file_override, keys, ikwid)
        case 'age': handleAgeRem(sops_file_override, keys, ikwid)
        case _:
            console.print("No available type passed. Exiting.")
            return
    confirm = True if ikwid else Confirm.ask("Do you wish to update all encrypted files with the new keys?", default=True)
    if confirm:
        handleUpdateAllSecrets(args)

def listFp(args):
    GLOBAL_CONFIG_DIR = os.path.expanduser("~/.config/chaos")
    GLOBAL_CONFIG_FILE_PATH = os.path.join(GLOBAL_CONFIG_DIR, "config.yml")
    global_config = {}

    if os.path.exists(GLOBAL_CONFIG_FILE_PATH):
        global_config = OmegaConf.load(GLOBAL_CONFIG_FILE_PATH) or OmegaConf.create()

    sops_file_override = None
    if hasattr(args, 'sops_file_override') and args.sops_file_override:
        sops_file_override = args.sops_file_override
    else:
        sops_file_override = global_config.get('sops_file')

    if not sops_file_override:
        console.print("[bold red]ERROR:[/] No sops config file found. Exiting")
        sys.exit(1)

    match args.type:
        case 'pgp': results = listPgp(sops_file_override)
        case 'age': results = listAge(sops_file_override)
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
