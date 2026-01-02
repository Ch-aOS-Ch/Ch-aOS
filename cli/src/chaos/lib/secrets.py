from io import StringIO
from rich.console import Console
from omegaconf import OmegaConf, ListConfig, DictConfig
from chaos.lib.checkers import is_vault_in_use, check_vault_auth
from chaos.lib.secret_backends.utils import get_sops_files, _handle_provider_arg
import os
import math
import subprocess

console = Console()

"""
Module for handling secret management operations such as adding/removing keys, editing secrets, and printing secrets.

Better than ansible vault, like a bowss (jk).
"""

"""
Adds a new key to the sops config file and (if -u), updates all secrets.

Check secret_backends/utils.py for shared functions + their docs.
"""
def handleRotateAdd(args):
    sops_file_override = getattr(args, 'sops_file_override', None)
    secrets_file_override = getattr(args, 'secrets_file_override', None)
    team = getattr(args, 'team', None)

    _, sops_file_override, _ = get_sops_files(sops_file_override, secrets_file_override, team)

    keys = args.keys

    if not sops_file_override:
        raise FileNotFoundError("No sops config file found.")

    match args.type:
        case 'pgp':
            from chaos.lib.secret_backends.pgp import handlePgpAdd
            handlePgpAdd(args, sops_file_override, keys)
        case 'age':
            from chaos.lib.secret_backends.age import handleAgeAdd
            handleAgeAdd(args, sops_file_override, keys)
        case 'vault':
            from chaos.lib.secret_backends.vault import handleVaultAdd
            handleVaultAdd(args, sops_file_override, keys)
        case _:
            raise ValueError("No available type passed.")
    ikwid = args.i_know_what_im_doing

    confirm = True if ikwid else False
    if confirm:
        from chaos.lib.secret_backends.utils import handleUpdateAllSecrets
        handleUpdateAllSecrets(args)

"""Removes a key from the sops config file and (if -u), updates all secrets."""
def handleRotateRemove(args):
    sops_file_override = getattr(args, 'sops_file_override', None)
    secrets_file_override = getattr(args, 'secrets_file_override', None)
    team = getattr(args, 'team', None)

    _, sops_file_override, _ = get_sops_files(sops_file_override, secrets_file_override, team)

    keys = args.keys

    if not sops_file_override:
        raise FileNotFoundError("No sops config file found.")

    ikwid = args.i_know_what_im_doing
    match args.type:
        case 'pgp':
            from chaos.lib.secret_backends.pgp import handlePgpRem
            handlePgpRem(args, sops_file_override, keys)
        case 'age':
            from chaos.lib.secret_backends.age import handleAgeRem
            handleAgeRem(args, sops_file_override, keys)
        case 'vault':
            from chaos.lib.secret_backends.vault import handleVaultRem
            handleVaultRem(args, sops_file_override, keys)
        case _:
            raise ValueError("No available type passed.")
    confirm = True if ikwid else False
    if confirm:
        from chaos.lib.secret_backends.utils import handleUpdateAllSecrets
        handleUpdateAllSecrets(args)

"""Lists all keys of a certain type from the sops config file."""
def listFp(args):
    from rich.panel import Panel
    from itertools import zip_longest
    from rich.align import Align
    from rich.table import Table
    sops_file_override = getattr(args, 'sops_file_override', None)
    secrets_file_override = getattr(args, 'secrets_file_override', None)
    team = getattr(args, 'team', None)

    _, sops_file_override, _ = get_sops_files(sops_file_override, secrets_file_override, team)

    if not sops_file_override:
        raise FileNotFoundError("No sops config file found.")

    match args.type:
        case 'pgp':
            from chaos.lib.secret_backends.pgp import listPgp
            results = listPgp(sops_file_override)
        case 'age':
            from chaos.lib.secret_backends.age import listAge
            results = listAge(sops_file_override)
        case 'vault':
            from chaos.lib.secret_backends.vault import listVault
            results = listVault(sops_file_override)
        case _:
            raise ValueError("No available type passed.")

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

"""Sets or removes the Shamir threshold for a given creation rule in the sops config file."""
def handleSetShamir(args):
    sops_file_override = getattr(args, 'sops_file_override', None)
    secrets_file_override = getattr(args, 'secrets_file_override', None)
    team = getattr(args, 'team', None)

    _, sops_file_override, _ = get_sops_files(sops_file_override, secrets_file_override, team)

    if not sops_file_override:
        raise FileNotFoundError("No sops config file found.")

    if not os.path.exists(sops_file_override):
        raise FileNotFoundError(f"Sops config file does not exist at path: {sops_file_override}")

    threshold: int = args.share
    rule_index: int = args.index
    ikwid = getattr(args, 'i_know_what_im_doing', False)

    try:
        config_data = OmegaConf.load(sops_file_override)
        creation_rules = config_data.get('creation_rules')

        if not creation_rules:
            raise ValueError(f"No 'creation_rules' found in {sops_file_override}. Cannot set Shamir threshold.")

        if not (0 <= rule_index < len(creation_rules)):
            raise ValueError(f"Invalid rule index {rule_index}. Must be between 0 and {len(creation_rules) - 1}.")

        rule = creation_rules[rule_index]
        key_groups = rule.get('key_groups', [])
        num_key_groups = len(key_groups)

        if threshold <= 0:
            if rule.get('shamir_threshold') is not None:
                confirm = True if ikwid else False

                if confirm:
                    del rule['shamir_threshold']
                    OmegaConf.save(config_data, sops_file_override)
                    console.print(f"[bold green]Successfully removed Shamir threshold from rule {rule_index} in {sops_file_override}[/]")
                    confirm_update = True if ikwid else False
                    if confirm_update:
                        from chaos.lib.secret_backends.utils import handleUpdateAllSecrets
                        handleUpdateAllSecrets(args)
                else:
                    console.print("Aborting.")
            else:
                console.print(f"No Shamir threshold to remove from rule {rule_index}.")

            return

        if num_key_groups < 2:
            raise ValueError(f"Shamir threshold requires at least 2 key groups for rule {rule_index}, but only {num_key_groups} is defined.")

        if not (1 <= threshold <= num_key_groups):
            raise ValueError(f"Shamir threshold ({threshold}) must be between 1 and the number of key groups ({num_key_groups}).")

        rule['shamir_threshold'] = threshold

        OmegaConf.save(config=config_data, f=sops_file_override)

        console.print(f"[bold green]Successfully set Shamir threshold to {threshold} for rule {rule_index} in {sops_file_override}[/]")

        confirm = True if ikwid else False
        if confirm:
            from chaos.lib.secret_backends.utils import handleUpdateAllSecrets
            handleUpdateAllSecrets(args)

    except Exception as e:
        raise RuntimeError(f"Failed to update sops config file: {e}") from e

"""Opens the secrets file in SOPS for editing."""
def handleSecEdit(args):
    team = args.team
    op, keyPath = args.from_op if args.from_op else (None, None)
    sops_file_override = args.sops_file_override
    secrets_file_override = args.secrets_file_override
    secretsFile, sopsFile, global_config = get_sops_files(sops_file_override, secrets_file_override, team)

    args = _handle_provider_arg(args, global_config)

    bw, bw_keyType = (None, None)
    bws, bws_keyType = (None, None)
    op, op_keyType = (None, None)

    if hasattr(args, 'from_bw') and args.from_bw and None not in args.from_bw:
        bw, bw_keyType = args.from_bw
    if hasattr(args, 'from_bws') and args.from_bws and None not in args.from_bws:
        bws, bws_keyType = args.from_bws
    if hasattr(args, 'from_op') and args.from_op and None not in args.from_op:
        op, op_keyType = args.from_op

    if is_vault_in_use(sopsFile):
        is_authed, message = check_vault_auth()
        if not is_authed:
            raise PermissionError(message)

    if not secretsFile or not sopsFile:
        raise FileNotFoundError("SOPS check requires both secrets file and sops config file paths.\n"
                            "       Configure them using 'chaos set sec' and 'chaos set sops', or pass them with '-sf' and '-ss'.")

    try:
        isSops = args.sops
        if isSops:
            editor = os.getenv('EDITOR', 'nano')
            subprocess.run([editor, sopsFile], check=True)
        elif bws and bws_keyType:
            from chaos.lib.secret_backends.bws import bwsSopsEdit
            bwsSopsEdit(args)
        elif bw and bw_keyType:
            from chaos.lib.secret_backends.bw import bwSopsEdit
            bwSopsEdit(args)
        elif op and op_keyType:
            from chaos.lib.secret_backends.op import opSopsEdit
            opSopsEdit(args)
        else:
            subprocess.run(['sops', '--config', sopsFile, secretsFile], check=True)

    except subprocess.CalledProcessError as e:
        if e.returncode == 200: # sops exit code for no changes
            console.print("File has not changed, exiting.")
            return
        else:
            raise RuntimeError(f"SOPS editing failed with exit code {e.returncode}.") from e
    except FileNotFoundError as e:
        raise FileNotFoundError("'sops' command not found. Please ensure sops is installed and in your PATH.") from e

"""Prints the decrypted secrets file to stdout."""
def handleSecPrint(args):
    team = args.team
    isSops = args.sops
    op, keyPath = args.from_op if args.from_op else (None, None)
    sops_file_override = args.sops_file_override
    secrets_file_override = args.secrets_file_override
    secretsFile, sopsFile, global_config = get_sops_files(sops_file_override, secrets_file_override, team)

    args = _handle_provider_arg(args, global_config)

    bw, bw_keyType = (None, None)
    bws, bws_keyType = (None, None)
    op, op_keyType = (None, None)

    if hasattr(args, 'from_bw') and args.from_bw and None not in args.from_bw:
        bw, bw_keyType = args.from_bw
    if hasattr(args, 'from_bws') and args.from_bws and None not in args.from_bws:
        bws, bws_keyType = args.from_bws
    if hasattr(args, 'from_op') and args.from_op and None not in args.from_op:
        op, op_keyType = args.from_op

    if not isSops:
        if not secretsFile:
            raise FileNotFoundError("SOPS check requires a secrets file path.\n"
                                "       Configure one using 'chaos set secrets', or pass it with '-sf'.")
    if not sopsFile:
        raise FileNotFoundError("SOPS check requires a sops config file path.\n"
                            "       Configure one using 'chaos set sops', or pass it with '-ss'.")

    if is_vault_in_use(sopsFile):
        is_authed, message = check_vault_auth()
        if not is_authed:
            raise PermissionError(message)

    try:
        if isSops:
            subprocess.run(['cat', sopsFile], check=True)
        elif bws and bws_keyType:
            from chaos.lib.secret_backends.bws import bwsSopsDec
            sopsDecryptResult = bwsSopsDec(args)
            print(sopsDecryptResult.stdout)
        elif bw and bw_keyType:
            from chaos.lib.secret_backends.bw import bwSopsDec
            sopsDecryptResult = bwSopsDec(args)
            print(sopsDecryptResult.stdout)
        elif op and op_keyType:
            from chaos.lib.secret_backends.op import opSopsDec
            sopsDecryptResult = opSopsDec(args)
            print(sopsDecryptResult.stdout)
        else:
            # if op and keyPath:
            #     from chaos.lib.secret_backends.op import opSopsDec
            #     sopsDecryptResult = opSopsDec(args)
            #     print(sopsDecryptResult.stdout)
            # else:
                subprocess.run(['sops', '--config', sopsFile, '--decrypt', secretsFile], check=True)
    except subprocess.CalledProcessError as e:
        details = e.stderr.decode() if e.stderr else "No output."
        raise RuntimeError(f"SOPS decryption failed.\nDetails: {details}") from e
    except FileNotFoundError as e:
        raise FileNotFoundError("'sops' command not found. Please ensure sops is installed and in your PATH.") from e

"""Prints specific keys from the decrypted secrets file to stdout."""
def handleSecCat(args):
    team = args.team
    op, keyPath = args.from_op if args.from_op else (None, None)
    sops_file_override = args.sops_file_override
    keys = args.keys
    secrets_file_override = args.secrets_file_override
    secretsFile, sopsFile, global_config = get_sops_files(sops_file_override, secrets_file_override, team)

    args = _handle_provider_arg(args, global_config)

    bw, bw_keyType = (None, None)
    bws, bws_keyType = (None, None)
    op, op_keyType = (None, None)

    if hasattr(args, 'from_bw') and args.from_bw and None not in args.from_bw:
        bw, bw_keyType = args.from_bw
    if hasattr(args, 'from_bws') and args.from_bws and None not in args.from_bws:
        bws, bws_keyType = args.from_bws
    if hasattr(args, 'from_op') and args.from_op and None not in args.from_op:
        op, op_keyType = args.from_op

    if not secretsFile or not sopsFile:
        raise FileNotFoundError("SOPS check requires both secrets file and sops config file paths.\n"
                            "       Configure them using 'chaos -sec' and 'chaos -sops', or pass them with '-sf' and '-ss'.")

    if is_vault_in_use(sopsFile):
        is_authed, message = check_vault_auth()
        if not is_authed:
            raise PermissionError(message)

    try:
        isSops = args.sops
        sopsDecryptResult = None
        if not isSops:
            if bws and bws_keyType:
                from chaos.lib.secret_backends.bws import bwsSopsDec
                sopsDecryptResult = bwsSopsDec(args)
            elif bw and bw_keyType:
                from chaos.lib.secret_backends.bw import bwSopsDec
                sopsDecryptResult = bwSopsDec(args)
            elif op and op_keyType:
                from chaos.lib.secret_backends.op import opSopsDec
                sopsDecryptResult = opSopsDec(args)
            else:
                sopsDecryptResult = subprocess.run(['sops', '--config', sopsFile, '--decrypt', secretsFile], check=True, text=True, capture_output=True)
        else:
            sopsDecryptResult = subprocess.run(['cat', sopsFile], check=True, text=True, capture_output=True)

        if sopsDecryptResult is None:
            raise RuntimeError("SOPS decryption result is None. This should not happen.")

        ocLoadResult = OmegaConf.load(StringIO(sopsDecryptResult.stdout))
        isJson = args.json
        for key in keys:
            value = OmegaConf.select(ocLoadResult, key, default=None)
            if value is None:
                console.print(f"[bold yellow]WARNING:[/]{key} not found in {secretsFile}.")
                continue

            if not isJson:
                if isinstance(value, (DictConfig, ListConfig)):
                    container = OmegaConf.create({key: value})
                    print(f"{OmegaConf.to_yaml(container)}")
                else:
                    print(f"{key}: {value}")
            else:
                output_value = str(value)
                print(f"{key}: {output_value}")
    except subprocess.CalledProcessError as e:
        details = e.stderr if e.stderr else "No output."
        raise RuntimeError(f"SOPS decryption failed.\nDetails: {details}") from e
    except FileNotFoundError as e:
        raise FileNotFoundError("'sops' command not found. Please ensure sops is installed and in your PATH.") from e
