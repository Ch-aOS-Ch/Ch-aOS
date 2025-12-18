import re
import subprocess
import sys
from omegaconf import OmegaConf
from rich.console import Console
from chaos.lib.secret_backends.utils import flatten
from rich.prompt import Confirm

console = Console()

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
