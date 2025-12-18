import re
import sys
from omegaconf import OmegaConf
from rich.prompt import Confirm
from rich.console import Console
from chaos.lib.secret_backends.utils import flatten

console = Console()


def is_valid_age_key(key):
    return re.fullmatch(r"age1[a-z0-9]{58}", key)

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
