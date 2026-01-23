from typing import cast

"""
Module for handling secret management operations such as adding/removing keys, editing secrets, and printing secrets.
"""


def handleRotateAdd(args):
    """
    Adds a new key to the sops config file and (if -u), updates all secrets.

    Check secret_backends/utils.py for shared functions + their docs.
    """
    from chaos.lib.secret_backends.utils import get_sops_files
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

def handleRotateRemove(args):
    """Removes a key from the sops config file and (if -u), updates all secrets."""
    from chaos.lib.secret_backends.utils import get_sops_files
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

def listFp(args):
    """Lists all keys of a certain type from the sops config file."""
    from chaos.lib.secret_backends.utils import get_sops_files
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

        if results:
            from chaos.lib.utils import render_list_as_table
            title = f"[italic][green]Found {args.type} Keys:[/][/]"
            render_list_as_table(list(results), title)

def handleSetShamir(args):
    """Sets or removes the Shamir threshold for a given creation rule in the sops config file."""
    from rich.console import Console
    from chaos.lib.secret_backends.utils import get_sops_files
    import os
    console = Console()
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
        from omegaconf import OmegaConf, DictConfig
        config_data = OmegaConf.load(sops_file_override)
        config_data = cast(DictConfig, config_data)
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

def handleSecEdit(args):
    """Opens the secrets file in SOPS for editing."""
    from chaos.lib.secret_backends.utils import get_sops_files,  _resolveProvider
    import subprocess
    from chaos.lib.checkers import is_vault_in_use
    import os
    team = args.team
    sops_file_override = args.sops_file_override
    secrets_file_override = args.secrets_file_override
    secretsFile, sopsFile, global_config = get_sops_files(sops_file_override, secrets_file_override, team)

    provider = _resolveProvider(args, global_config)

    if is_vault_in_use(sopsFile):
        from chaos.lib.checkers import check_vault_auth
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
        elif provider:
            provider.edit(secretsFile, sopsFile)
        else:
            subprocess.run(['sops', '--config', sopsFile, secretsFile], check=True)

    except subprocess.CalledProcessError as e:
        from rich.console import Console
        console = Console()
        if e.returncode == 200: # sops exit code for no changes
            console.print("File has not changed, exiting.")
            return
        else:
            raise RuntimeError(f"SOPS editing failed with exit code {e.returncode}.") from e
    except FileNotFoundError as e:
        raise FileNotFoundError("'sops' command not found. Please ensure sops is installed and in your PATH.") from e

def handleSecPrint(args):
    """Prints the decrypted secrets file to stdout."""
    import json
    import subprocess
    from chaos.lib.checkers import is_vault_in_use
    from chaos.lib.secret_backends.utils import get_sops_files, _handle_provider_arg
    team = args.team
    isSops = args.sops
    sops_file_override = args.sops_file_override
    secrets_file_override = args.secrets_file_override
    secretsFile, sopsFile, global_config = get_sops_files(sops_file_override, secrets_file_override, team)

    args = _handle_provider_arg(args, global_config)

    if not isSops:
        if not secretsFile:
            raise FileNotFoundError("SOPS check requires a secrets file path.\n"
                                "       Configure one using 'chaos set secrets', or pass it with '-sf'.")
    if not sopsFile:
        raise FileNotFoundError("SOPS check requires a sops config file path.\n"
                            "       Configure one using 'chaos set sops', or pass it with '-ss'.")

    if is_vault_in_use(sopsFile):
        from chaos.lib.checkers import check_vault_auth
        is_authed, message = check_vault_auth()
        if not is_authed:
            raise PermissionError(message)

    try:
        if isSops:
            decrypted_output = subprocess.run(['cat', sopsFile], check=True, capture_output=True, text=True).stdout
        else:
            from .secret_backends.utils import decrypt_secrets
            decrypted_output = decrypt_secrets(secretsFile, sopsFile, global_config, args)
        if args.json:
            from omegaconf import OmegaConf
            decrypted_output = json.dumps(OmegaConf.to_container(OmegaConf.create(decrypted_output), resolve=True), indent=2)
        print(decrypted_output)
    except subprocess.CalledProcessError as e:
        details = e.stderr.decode() if e.stderr else "No output."
        raise RuntimeError(f"SOPS decryption failed.\nDetails: {details}") from e
    except FileNotFoundError as e:
        raise FileNotFoundError("'sops' command not found. Please ensure sops is installed and in your PATH.") from e

def handleSecCat(args):
    """Prints specific keys from the decrypted secrets file to stdout."""
    from chaos.lib.checkers import is_vault_in_use
    from chaos.lib.secret_backends.utils import get_sops_files, _handle_provider_arg
    import json
    import subprocess
    from io import StringIO
    team = args.team
    sops_file_override = args.sops_file_override
    keys = args.keys
    secrets_file_override = args.secrets_file_override
    secretsFile, sopsFile, global_config = get_sops_files(sops_file_override, secrets_file_override, team)

    args = _handle_provider_arg(args, global_config)

    if not secretsFile or not sopsFile:
        raise FileNotFoundError("SOPS check requires both secrets file and sops config file paths.\n"
                            "       Configure them using 'chaos -sec' and 'chaos -sops', or pass them with '-sf' and '-ss'.")

    if is_vault_in_use(sopsFile):
        from chaos.lib.checkers import check_vault_auth
        is_authed, message = check_vault_auth()
        if not is_authed:
            raise PermissionError(message)

    try:
        isSops = args.sops
        sopsDecryptResult = None
        if isSops:
            sopsDecryptResult = subprocess.run(['cat', sopsFile], check=True, text=True, capture_output=True).stdout
        else:
            from .secret_backends.utils import decrypt_secrets
            sopsDecryptResult = decrypt_secrets(secretsFile, sopsFile, global_config, args)

        if sopsDecryptResult is None:
            raise RuntimeError("SOPS decryption result is None. This should not happen.")

        from omegaconf import OmegaConf, ListConfig, DictConfig
        ocLoadResult = OmegaConf.load(StringIO(sopsDecryptResult))
        isJson = args.json
        for key in keys:
            value = OmegaConf.select(ocLoadResult, key, default=None)
            if value is None:
                from rich.console import Console
                console = Console()
                console.print(f"[bold yellow]WARNING:[/]{key} not found in {secretsFile}.")
                continue

            if args.value:
                print (value)
                continue

            if not isJson:
                if isinstance(value, (DictConfig, ListConfig)):
                    container = OmegaConf.create({key: value})
                    print(f"{OmegaConf.to_yaml(container)}")
                else:
                    output_value = str(value)
                    print(f"{key}: {output_value}")
            else:
                print(json.dumps(OmegaConf.to_container(OmegaConf.create({key: value})), indent=2))
    except subprocess.CalledProcessError as e:
        details = e.stderr if e.stderr else "No output."
        raise RuntimeError(f"SOPS decryption failed.\nDetails: {details}") from e
    except FileNotFoundError as e:
        raise FileNotFoundError("'sops' command not found. Please ensure sops is installed and in your PATH.") from e

def handleExportSec(args, global_config):
    from chaos.lib.secret_backends.utils import _getProviderByName
    provider_subcommand_name = args.export_commands
    provider = _getProviderByName(provider_subcommand_name, args, global_config)
    provider.export_secrets()

def handleImportSec(args, global_config):
    from chaos.lib.secret_backends.utils import _getProviderByName
    provider_subcommand_name = args.import_commands
    provider = _getProviderByName(provider_subcommand_name, args, global_config)
    provider.import_secrets()

