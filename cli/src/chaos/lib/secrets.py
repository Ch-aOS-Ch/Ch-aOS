from typing import cast

from chaos.lib.args.dataclasses import (
    DataGatherPayload,
    DataGatherRequest,
    ResultPayload,
    SecretsCatPayload,
    SecretsEditPayload,
    SecretsExportPayload,
    SecretsImportPayload,
    SecretsListPayload,
    SecretsPrintPayload,
    SecretsRotatePayload,
    SecretsSetShamirPayload,
)

"""
Module for handling secret management operations such as adding/removing keys, editing secrets, and printing secrets.
"""


def gatherRotateAdd(payload: SecretsRotatePayload) -> DataGatherRequest | None:
    if not payload.context.i_know_what_im_doing and not payload.update_confirmed:
        return DataGatherRequest(
            name="secrets_rotate_add",
            fields=[
                DataGatherPayload(
                    name="update_confirmed",
                    prompt="Do you want to update all existing secrets with the new keys?",
                    input_type="boolean",
                    required=True,
                    default=False,
                )
            ],
        )
    return None


def gatherRotateRemove(payload: SecretsRotatePayload) -> DataGatherRequest | None:
    if not payload.context.i_know_what_im_doing and not payload.update_confirmed:
        return DataGatherRequest(
            name="secrets_rotate_remove",
            fields=[
                DataGatherPayload(
                    name="update_confirmed",
                    prompt="Do you want to update all existing secrets to remove the keys?",
                    input_type="boolean",
                    required=True,
                    default=False,
                )
            ],
        )
    return None


def gatherSetShamir(payload: SecretsSetShamirPayload) -> DataGatherRequest | None:
    fields = []

    if (
        payload.share <= 0
        and not payload.context.i_know_what_im_doing
        and not payload.confirmed
    ):
        fields.append(
            DataGatherPayload(
                name="confirmed",
                prompt=f"Are you sure you want to remove the Shamir threshold for rule {payload.index}?",
                input_type="boolean",
                required=True,
                default=False,
            )
        )

    if not payload.context.i_know_what_im_doing and not payload.update_confirmed:
        fields.append(
            DataGatherPayload(
                name="update_confirmed",
                prompt="Do you want to update all existing secrets to apply the new Shamir threshold?",
                input_type="boolean",
                required=True,
                default=False,
            )
        )

    if fields:
        return DataGatherRequest(name="secrets_set_shamir", fields=fields)
    return None


def handleRotateAdd(payload: SecretsRotatePayload) -> ResultPayload:
    """
    Adds a new key to the sops config file and (if -u), updates all secrets.

    Check secret_backends/utils.py for shared functions + their docs.
    """
    from chaos.lib.secret_backends.utils import get_sops_files

    context = payload.context
    _, sops_file_override, _ = get_sops_files(
        context.sops_file_override, context.secrets_file_override, context.team
    )

    keys = payload.keys

    if not sops_file_override:
        return ResultPayload(success=False, error=["No sops config file found."])

    messages = []
    errors = []

    match payload.type:
        case "pgp":
            from chaos.lib.secret_backends.pgp import handlePgpAdd

            msgs, errs = handlePgpAdd(payload, sops_file_override, keys)
            messages.extend(msgs)
            errors.extend(errs)
        case "age":
            from chaos.lib.secret_backends.age import handleAgeAdd

            msgs, errs = handleAgeAdd(payload, sops_file_override, keys)
            messages.extend(msgs)
            errors.extend(errs)
        case "vault":
            from chaos.lib.secret_backends.vault import handleVaultAdd

            msgs, errs = handleVaultAdd(payload, sops_file_override, keys)
            messages.extend(msgs)
            errors.extend(errs)

    if (context.i_know_what_im_doing or payload.update_confirmed) and not errors:
        from chaos.lib.secret_backends.utils import handleUpdateAllSecrets

        upd_msgs, upd_errs = handleUpdateAllSecrets(context)
        messages.extend(upd_msgs)
        errors.extend(upd_errs)

    return ResultPayload(success=len(errors) == 0, message=messages, error=errors)


def handleRotateRemove(payload: SecretsRotatePayload) -> ResultPayload:
    """Removes a key from the sops config file and (if -u), updates all secrets."""
    from chaos.lib.secret_backends.utils import get_sops_files

    context = payload.context
    _, sops_file_override, _ = get_sops_files(
        context.sops_file_override, context.secrets_file_override, context.team
    )

    keys = payload.keys

    if not sops_file_override:
        return ResultPayload(success=False, error=["No sops config file found."])

    messages = []
    errors = []

    match payload.type:
        case "pgp":
            from chaos.lib.secret_backends.pgp import handlePgpRem

            msgs, errs = handlePgpRem(payload, sops_file_override, keys)
            messages.extend(msgs)
            errors.extend(errs)
        case "age":
            from chaos.lib.secret_backends.age import handleAgeRem

            msgs, errs = handleAgeRem(payload, sops_file_override, keys)
            messages.extend(msgs)
            errors.extend(errs)
        case "vault":
            from chaos.lib.secret_backends.vault import handleVaultRem

            msgs, errs = handleVaultRem(payload, sops_file_override, keys)
            messages.extend(msgs)
            errors.extend(errs)

    if (context.i_know_what_im_doing or payload.update_confirmed) and not errors:
        from chaos.lib.secret_backends.utils import handleUpdateAllSecrets

        upd_msgs, upd_errs = handleUpdateAllSecrets(context)
        messages.extend(upd_msgs)
        errors.extend(upd_errs)

    return ResultPayload(success=len(errors) == 0, message=messages, error=errors)


def listFp(payload: SecretsListPayload) -> ResultPayload:
    """Lists all keys of a certain type from the sops config file."""
    from chaos.lib.secret_backends.utils import get_sops_files

    results = None
    messages = []
    errors = []

    context = payload.context
    _, sops_file_override, _ = get_sops_files(
        context.sops_file_override, context.secrets_file_override, context.team
    )

    if not sops_file_override:
        raise FileNotFoundError("No sops config file found.")

    match payload.type:
        case "pgp":
            from chaos.lib.secret_backends.pgp import listPgp

            results, warnings, errors, messages = listPgp(sops_file_override)
        case "age":
            from chaos.lib.secret_backends.age import listAge

            results, warnings, errors, messages = listAge(sops_file_override)
        case "vault":
            from chaos.lib.secret_backends.vault import listVault

            results, warnings, errors, messages = listVault(sops_file_override)

    response = ResultPayload(
        success=True if not errors else False,
        message=[f"Listed {payload.type} keys successfully."]
        if not messages
        else messages,
        data=results,
        error=errors if errors else None,
    )

    return response


def handleSetShamir(payload: SecretsSetShamirPayload) -> ResultPayload:
    """Sets or removes the Shamir threshold for a given creation rule in the sops config file."""
    import os

    from chaos.lib.secret_backends.utils import get_sops_files

    context = payload.context
    _, sops_file_override, _ = get_sops_files(
        context.sops_file_override, context.secrets_file_override, context.team
    )

    if not sops_file_override:
        return ResultPayload(success=False, error=["No sops config file found."])

    if not os.path.exists(sops_file_override):
        return ResultPayload(
            success=False,
            error=[f"Sops config file does not exist at path: {sops_file_override}"],
        )

    threshold: int = payload.share
    rule_index: int = payload.index
    ikwid = context.i_know_what_im_doing

    messages = []
    errors = []

    try:
        from omegaconf import DictConfig, OmegaConf

        config_data = OmegaConf.load(sops_file_override)
        config_data = cast(DictConfig, config_data)
        creation_rules = config_data.get("creation_rules")

        if not creation_rules:
            return ResultPayload(
                success=False,
                error=[
                    f"No 'creation_rules' found in {sops_file_override}. Cannot set Shamir threshold."
                ],
            )

        if not (0 <= rule_index < len(creation_rules)):
            return ResultPayload(
                success=False,
                error=[
                    f"Invalid rule index {rule_index}. Must be between 0 and {len(creation_rules) - 1}."
                ],
            )

        rule = creation_rules[rule_index]
        key_groups = rule.get("key_groups", [])
        num_key_groups = len(key_groups)

        if threshold <= 0:
            if rule.get("shamir_threshold") is not None:
                confirm = True if (ikwid or payload.confirmed) else False

                if confirm:
                    del rule["shamir_threshold"]
                    OmegaConf.save(config_data, sops_file_override)
                    messages.append(
                        f"Successfully removed Shamir threshold from rule {rule_index} in {sops_file_override}"
                    )
                    confirm_update = (
                        True if (ikwid or payload.update_confirmed) else False
                    )
                    if confirm_update:
                        from chaos.lib.secret_backends.utils import (
                            handleUpdateAllSecrets,
                        )

                        upd_msgs, upd_errs = handleUpdateAllSecrets(context)
                        messages.extend(upd_msgs)
                        errors.extend(upd_errs)
                else:
                    messages.append("Aborting.")
            else:
                messages.append(
                    f"No Shamir threshold to remove from rule {rule_index}."
                )

            return ResultPayload(
                success=len(errors) == 0, message=messages, error=errors
            )

        if num_key_groups < 2:
            return ResultPayload(
                success=False,
                error=[
                    f"Shamir threshold requires at least 2 key groups for rule {rule_index}, but only {num_key_groups} is defined."
                ],
            )

        if not (1 <= threshold <= num_key_groups):
            return ResultPayload(
                success=False,
                error=[
                    f"Shamir threshold ({threshold}) must be between 1 and the number of key groups ({num_key_groups})."
                ],
            )

        rule["shamir_threshold"] = threshold

        OmegaConf.save(config=config_data, f=sops_file_override)

        messages.append(
            f"Successfully set Shamir threshold to {threshold} for rule {rule_index} in {sops_file_override}"
        )

        confirm = True if (ikwid or payload.update_confirmed) else False
        if confirm:
            from chaos.lib.secret_backends.utils import handleUpdateAllSecrets

            upd_msgs, upd_errs = handleUpdateAllSecrets(context)
            messages.extend(upd_msgs)
            errors.extend(upd_errs)

    except Exception as e:
        return ResultPayload(
            success=False, error=[f"Failed to update sops config file: {e}"]
        )
    return ResultPayload(success=len(errors) == 0, message=messages, error=errors)


def handleSecEdit(payload: SecretsEditPayload):
    """Opens the secrets file in SOPS for editing."""
    import os
    import subprocess

    from chaos.lib.secret_backends.crypto import is_vault_in_use
    from chaos.lib.secret_backends.utils import _resolveProvider, get_sops_files

    context = payload.context
    secretsFile, sopsFile, global_config = get_sops_files(
        context.sops_file_override, context.secrets_file_override, context.team
    )

    provider = _resolveProvider(context, global_config)

    if is_vault_in_use(sopsFile):
        from chaos.lib.secret_backends.crypto import check_vault_auth

        is_authed, message = check_vault_auth()
        if not is_authed:
            raise PermissionError(message)

    if not secretsFile or not sopsFile:
        raise FileNotFoundError(
            "SOPS check requires both secrets file and sops config file paths.\n"
            "       Configure them using 'chaos set sec' and 'chaos set sops', or pass them with '-sf' and '-ss'."
        )

    try:
        if payload.edit_sops_file:
            editor = os.getenv("EDITOR", "nano")
            subprocess.run([editor, sopsFile], check=True)
        elif provider:
            provider.edit(secretsFile, sopsFile)
        else:
            subprocess.run(["sops", "--config", sopsFile, secretsFile], check=True)

    except subprocess.CalledProcessError as e:
        from rich.console import Console

        console = Console()
        if e.returncode == 200:  # sops exit code for no changes
            console.print("File has not changed, exiting.")
            return
        else:
            raise RuntimeError(
                f"SOPS editing failed with exit code {e.returncode}."
            ) from e
    except FileNotFoundError as e:
        raise FileNotFoundError(
            "'sops' command not found. Please ensure sops is installed and in your PATH."
        ) from e


def handleSecPrint(payload: SecretsPrintPayload):
    """Prints the decrypted secrets file to stdout."""
    import json
    import subprocess

    from chaos.lib.secret_backends.crypto import is_vault_in_use
    from chaos.lib.secret_backends.utils import _handle_provider_arg, get_sops_files

    context = payload.context
    secretsFile, sopsFile, global_config = get_sops_files(
        context.sops_file_override, context.secrets_file_override, context.team
    )

    context = _handle_provider_arg(context, global_config)

    if not payload.print_sops_file:
        if not secretsFile:
            raise FileNotFoundError(
                "SOPS check requires a secrets file path.\n"
                "       Configure one using 'chaos set secrets', or pass it with '-sf'."
            )
    if not sopsFile:
        raise FileNotFoundError(
            "SOPS check requires a sops config file path.\n"
            "       Configure one using 'chaos set sops', or pass it with '-ss'."
        )

    if is_vault_in_use(sopsFile):
        from chaos.lib.secret_backends.crypto import check_vault_auth

        is_authed, message = check_vault_auth()
        if not is_authed:
            raise PermissionError(message)

    try:
        if payload.print_sops_file:
            decrypted_output = subprocess.run(
                ["cat", sopsFile], check=True, capture_output=True, text=True
            ).stdout
        else:
            from .secret_backends.utils import decrypt_secrets

            decrypted_output = decrypt_secrets(
                secretsFile, sopsFile, global_config, context
            )
        if payload.as_json:
            from omegaconf import OmegaConf

            decrypted_output = json.dumps(
                OmegaConf.to_container(
                    OmegaConf.create(decrypted_output), resolve=True
                ),
                indent=2,
            )
        print(decrypted_output)
    except subprocess.CalledProcessError as e:
        details = e.stderr.decode() if e.stderr else "No output."
        raise RuntimeError(f"SOPS decryption failed.\nDetails: {details}") from e
    except FileNotFoundError as e:
        raise FileNotFoundError(
            "'sops' command not found. Please ensure sops is installed and in your PATH."
        ) from e


def handleSecCat(payload: SecretsCatPayload):
    """Prints specific keys from the decrypted secrets file to stdout."""
    import json
    import subprocess
    from io import StringIO

    from chaos.lib.secret_backends.crypto import is_vault_in_use
    from chaos.lib.secret_backends.utils import _handle_provider_arg, get_sops_files

    context = payload.context
    secretsFile, sopsFile, global_config = get_sops_files(
        context.sops_file_override, context.secrets_file_override, context.team
    )

    context = _handle_provider_arg(context, global_config)

    if not secretsFile or not sopsFile:
        raise FileNotFoundError(
            "SOPS check requires both secrets file and sops config file paths.\n"
            "       Configure them using 'chaos -sec' and 'chaos -sops', or pass them with '-sf' and '-ss'."
        )

    if is_vault_in_use(sopsFile):
        from chaos.lib.secret_backends.crypto import check_vault_auth

        is_authed, message = check_vault_auth()
        if not is_authed:
            raise PermissionError(message)

    try:
        sopsDecryptResult = None
        if payload.cat_sops_file:
            sopsDecryptResult = subprocess.run(
                ["cat", sopsFile], check=True, text=True, capture_output=True
            ).stdout
        else:
            from .secret_backends.utils import decrypt_secrets

            sopsDecryptResult = decrypt_secrets(
                secretsFile, sopsFile, global_config, context
            )

        if sopsDecryptResult is None:
            raise RuntimeError(
                "SOPS decryption result is None. This should not happen."
            )

        from omegaconf import DictConfig, ListConfig, OmegaConf

        ocLoadResult = OmegaConf.load(StringIO(sopsDecryptResult))
        for key in payload.keys:
            value = OmegaConf.select(ocLoadResult, key, default=None)
            if value is None:
                from rich.console import Console

                console = Console()
                console.print(
                    f"[bold yellow]WARNING:[/]{key} not found in {secretsFile}."
                )
                continue

            if payload.value_only:
                print(value)
                continue

            if not payload.as_json:
                if isinstance(value, (DictConfig, ListConfig)):
                    container = OmegaConf.create({key: value})
                    print(f"{OmegaConf.to_yaml(container)}")
                else:
                    output_value = str(value)
                    print(f"{key}: {output_value}")
            else:
                print(
                    json.dumps(
                        OmegaConf.to_container(OmegaConf.create({key: value})), indent=2
                    )
                )
    except subprocess.CalledProcessError as e:
        details = e.stderr if e.stderr else "No output."
        raise RuntimeError(f"SOPS decryption failed.\nDetails: {details}") from e
    except FileNotFoundError as e:
        raise FileNotFoundError(
            "'sops' command not found. Please ensure sops is installed and in your PATH."
        ) from e


def handleExportSec(payload: SecretsExportPayload, global_config):
    from chaos.lib.secret_backends.utils import _getProviderByName

    provider = _getProviderByName(payload, global_config)
    provider.export_secrets(payload)


def handleImportSec(payload: SecretsImportPayload, global_config):
    from chaos.lib.secret_backends.utils import _getProviderByName

    provider = _getProviderByName(payload, global_config)
    provider.import_secrets(payload)
