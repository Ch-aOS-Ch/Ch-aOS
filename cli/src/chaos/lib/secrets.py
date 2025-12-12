from rich.console import Console
import os
from rich.prompt import Confirm
import sys
import re
import subprocess
from omegaconf import OmegaConf, ListConfig
from pathlib import Path

console = Console()

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

    keys = args.pgp_keys

    if not sops_file_override:
        console.print("[bold red]ERROR:[/] No sops config file found. Exiting")
        sys.exit(1)

    server = args.pgp_server
    valids = set()
    for key in keys:
        clean_key = key.replace(" ", "")
        if len(clean_key) < 40:
            confirm = Confirm.ask(f"[bold yellow]WARNING:[/] Unsafe PGP key fingerprint: {key}. Are you sure you want to proceed?", default=False)
            if not confirm:
                continue

        if not is_valid_fp(clean_key):
            console.print(f"[bold red]ERROR:[/] Invalid PGP fingerprint: {key}. Skipping.")
            continue

        if not pgp_exists(clean_key):
            console.print(f"[bold yellow]WARNING:[/] PGP fingerprint {key} does not exist locally.")
            if not server:
                console.print(f"[bold red]ERROR:[/] PGP fingerprint {key} does not exist locally and no server was passed. Skipping")
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

    keys = args.pgp_keys

    if not sops_file_override:
        console.print("[bold red]ERROR:[/] No sops config file found. Exiting")
        sys.exit(1)

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

        console.print("Keys to remove:")
        for key in keys_to_remove:
            console.print(f"  {key}")

        confirm = Confirm.ask("Are you sure you want to remove these keys?", default=False)
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
