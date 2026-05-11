"""Module for handling secret management operations such as adding/removing keys, editing secrets, and printing secrets."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, cast

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

if TYPE_CHECKING:
    from typing import Literal, TypedDict

    from omegaconf import DictConfig

    from chaos.lib.secret_backends.providers.base import Provider

    class SecEditData(TypedDict):
        provider: Provider | None
        secrets_file: str
        sops_file: str


def gatherRotateAdd(payload: SecretsRotatePayload) -> DataGatherRequest | None:
    """Checks if confirmation is needed for rotating/adding keys.

    Args:
        payload (SecretsRotatePayload): The payload containing rotation options and context.

    Returns:
        DataGatherRequest | None: A request for user confirmation if required, else None.
    """
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
    """Checks if confirmation is needed for rotating/removing keys.

    Args:
        payload (SecretsRotatePayload): The payload containing rotation options and context.

    Returns:
        DataGatherRequest | None: A request for user confirmation if required, else None.
    """
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


def gatherImportSec(payload: SecretsImportPayload) -> DataGatherRequest | None:
    """Checks if confirmation is needed for importing keys.

    Args:
        payload (SecretsImportPayload): The payload containing import context.

    Returns:
        DataGatherRequest | None: A request for user confirmation if required, else None.
    """
    from pathlib import Path

    if payload.key_type == "age":
        currentPathAgeFile = Path.cwd() / "keys.txt"
        if currentPathAgeFile.exists() and not payload.confirmed:
            return DataGatherRequest(
                name="secrets_import_confirm",
                fields=[
                    DataGatherPayload(
                        name="confirmed",
                        prompt="A 'keys.txt' file already exists in the current directory. Do you want to overwrite it?",
                        input_type="boolean",
                        required=True,
                        default=False,
                    )
                ],
            )
    elif payload.key_type == "vault":
        currentVaultFile = Path.cwd() / "vault_keys.txt"
        if currentVaultFile.exists() and not payload.confirmed:
            return DataGatherRequest(
                name="secrets_import_confirm",
                fields=[
                    DataGatherPayload(
                        name="confirmed",
                        prompt="A 'vault_keys.txt' file already exists in the current directory. Do you want to overwrite it?",
                        input_type="boolean",
                        required=True,
                        default=False,
                    )
                ],
            )
    return None


def gatherSetShamir(payload: SecretsSetShamirPayload) -> DataGatherRequest | None:
    """Checks if confirmation is needed for setting/removing Shamir threshold.

    Args:
        payload (SecretsSetShamirPayload): The payload containing shamir settings context.

    Returns:
        DataGatherRequest | None: A request for user confirmation if required, else None.
    """
    fields: list[DataGatherPayload] = []

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


def handleRotateAdd(payload: SecretsRotatePayload) -> ResultPayload[None]:
    """Adds a new key to the sops config file and (if -u), updates all secrets.

    Args:
        payload (SecretsRotatePayload): The payload defining the rotation target and context.

    Returns:
        ResultPayload[None]: The result payload of the rotation add operation.

    Notes:
        Check `secret_backends/utils.py` for shared functions and their docs.
    """
    from chaos.lib.secret_backends.key_backends.factory import get_key_backend
    from chaos.lib.secret_backends.utils import get_sops_files

    context = payload.context
    _, sops_file_override, _ = get_sops_files(
        context.sops_file_override, context.secrets_file_override, context.team
    )

    keys = payload.keys

    if not sops_file_override:
        return ResultPayload(success=False, error=["No sops config file found."])

    messages: list[str] = []
    errors: list[str] = []

    backend = None

    try:
        backend = get_key_backend(payload.type)
    except ImportError as e:
        return ResultPayload(
            success=False, error=[f"Failed to get key backend: {str(e)}"]
        )
    except ValueError as e:
        return ResultPayload(success=False, error=[f"{str(e)}"])

    if backend is not None:
        msgs, errs = backend.handle_add(payload, sops_file_override, keys)
        errors.extend(errs)
        messages.extend(msgs)

    if (context.i_know_what_im_doing or payload.update_confirmed) and not errors:
        from chaos.lib.secret_backends.utils import handleUpdateAllSecrets

        upd_msgs, upd_errs = handleUpdateAllSecrets(context)
        messages.extend(upd_msgs)
        errors.extend(upd_errs)

    return ResultPayload(success=len(errors) == 0, message=messages, error=errors)


def handleRotateRemove(payload: SecretsRotatePayload) -> ResultPayload[None]:
    """Removes a key from the sops config file and (if -u), updates all secrets.

    Args:
        payload (SecretsRotatePayload): The payload defining the rotation removal target and context.

    Returns:
        ResultPayload[None]: The result payload of the rotation remove operation.
    """
    from chaos.lib.secret_backends.key_backends.factory import get_key_backend
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

    backend = None

    try:
        backend = get_key_backend(payload.type)
    except ImportError as e:
        return ResultPayload(
            success=False, error=[f"Failed to get key backend: {str(e)}"]
        )
    except ValueError as e:
        return ResultPayload(success=False, error=[f"{str(e)}"])

    if backend is not None:
        msgs, errs = backend.handle_rem(payload, sops_file_override, keys)
        errors.extend(errs)
        messages.extend(msgs)

    if (context.i_know_what_im_doing or payload.update_confirmed) and not errors:
        from chaos.lib.secret_backends.utils import handleUpdateAllSecrets

        upd_msgs, upd_errs = handleUpdateAllSecrets(context)
        messages.extend(upd_msgs)
        errors.extend(upd_errs)

    return ResultPayload(success=len(errors) == 0, message=messages, error=errors)


def listFp(payload: SecretsListPayload) -> ResultPayload[set[str]]:
    """Lists all keys of a certain type from the sops config file.

    Args:
        payload (SecretsListPayload): The payload defining the target type and context.

    Returns:
        ResultPayload[set[str]]: The result payload containing a set of key fingerprints or names.

    Raises:
        FileNotFoundError: If no sops config file is found.
    """
    from chaos.lib.secret_backends.key_backends.factory import get_key_backend
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

    try:
        try:
            backend = get_key_backend(payload.type)
        except ImportError as e:
            return ResultPayload(
                success=False, error=[f"Failed to get key backend: {str(e)}"]
            )
        except ValueError as e:
            return ResultPayload(success=False, error=[f"{str(e)}"])

        results, _, errs, msgs = backend.list_keys(sops_file_override)
        errors.extend(errs)
        messages.extend(msgs)
    except ValueError as e:
        errors.append(str(e))

    response = ResultPayload(
        success=True if not errors else False,
        message=[f"Listed {payload.type} keys successfully."]
        if not messages
        else messages,
        error=errors,
        data=results,
    )

    return response


def handleSetShamir(payload: SecretsSetShamirPayload) -> ResultPayload[None]:
    """Sets or removes the Shamir threshold for a given creation rule in the sops config file.

    Args:
        payload (SecretsSetShamirPayload): The payload containing the shamir configuration details.

    Returns:
        ResultPayload[None]: The result payload indicating success or failure.
    """
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
                    messages.append(
                        f"Shamir threshold removal for rule {rule_index} was not confirmed. No changes were made."
                    )
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


def handleSecEdit(payload: SecretsEditPayload) -> ResultPayload[SecEditData]:
    """Opens the secrets file in SOPS for editing.

    Args:
        payload (SecretsEditPayload): The payload containing context for editing secrets.

    Returns:
        ResultPayload[SecEditData]: The result payload containing related file paths and settings.
    """
    from chaos.lib.secret_backends.crypto import is_vault_in_use
    from chaos.lib.secret_backends.utils import _resolveProvider, get_sops_files

    errors = []
    messages = []

    context = payload.context
    secretsFile, sopsFile, global_config = get_sops_files(
        context.sops_file_override, context.secrets_file_override, context.team
    )

    provider = _resolveProvider(context, global_config)

    if is_vault_in_use(sopsFile):
        from chaos.lib.secret_backends.crypto import check_vault_auth

        is_authed, message = check_vault_auth()
        if not is_authed:
            errors.append(message)
            return ResultPayload(success=False, error=errors)

    if not secretsFile or not sopsFile:
        errors.append(
            "SOPS check requires both secrets file and sops config file paths.\n"
            "       Configure them using 'chaos set sec' and 'chaos set sops', or pass them with '-sf' and '-ss'."
        )
        return ResultPayload(success=False, error=errors)

    return ResultPayload(
        success=len(errors) == 0,
        message=messages,
        error=errors,
        data={
            "provider": provider,
            "secrets_file": secretsFile,
            "sops_file": sopsFile,
        },
    )


def handleSecPrint(payload: SecretsPrintPayload) -> ResultPayload[dict[str, str]]:
    """Decrypts the secrets file and returns the decrypted content as a string.

    Args:
        payload (SecretsPrintPayload): The payload indicating what to print.

    Returns:
        ResultPayload[dict[str, str]]: The result payload containing the decrypted content under 'dec'.
    """
    from chaos.lib.secret_backends.crypto import is_vault_in_use
    from chaos.lib.secret_backends.utils import _handle_provider_arg, get_sops_files

    context = payload.context
    secretsFile, sopsFile, global_config = get_sops_files(
        context.sops_file_override, context.secrets_file_override, context.team
    )

    context = _handle_provider_arg(context, global_config)

    errors = []
    messages = []

    if not payload.print_sops_file:
        if not secretsFile:
            errors.append(
                "SOPS check requires a secrets file path.\n"
                "       Configure one using 'chaos set secrets', or pass it with '-sf'."
            )
            return ResultPayload(success=False, error=errors)

    if not sopsFile:
        errors.append(
            "SOPS check requires a sops config file path.\n"
            "       Configure one using 'chaos set sops', or pass it with '-ss'."
        )
        return ResultPayload(success=False, error=errors)

    if is_vault_in_use(sopsFile):
        from chaos.lib.secret_backends.crypto import check_vault_auth

        is_authed, message = check_vault_auth()
        if not is_authed:
            errors.append(message)
            return ResultPayload(success=False, error=errors)

    import subprocess

    try:
        if payload.print_sops_file:
            decrypted_output = subprocess.run(
                ["cat", sopsFile],
                check=True,
                capture_output=True,
                text=True,
            ).stdout

        else:
            from .secret_backends.utils import decrypt_secrets

            decrypt_result = decrypt_secrets(
                secretsFile, sopsFile, global_config, context
            )

            if not decrypt_result.data:
                errors.append("Decryption failed. No output received.")
                return ResultPayload(success=False, message=messages, error=errors)

            if not decrypt_result.success:
                errors.extend(decrypt_result.error)
                return ResultPayload(success=False, message=messages, error=errors)

            decrypted_output = decrypt_result.data

        return ResultPayload(
            success=len(errors) == 0,
            message=messages,
            error=errors,
            data={"dec": decrypted_output},
        )

    except subprocess.CalledProcessError as e:
        details = e.stderr.decode() if e.stderr else "No output."
        errors.append(f"SOPS decryption failed.\nDetails: {details}")
        return ResultPayload(success=False, message=messages, error=errors)
    except FileNotFoundError:
        errors.append(
            "'sops' command not found. Please ensure sops is installed and in your PATH."
        )
        return ResultPayload(success=False, message=messages, error=errors)


def handleSecCat(
    payload: SecretsCatPayload,
) -> ResultPayload[dict[Literal["values"], list[tuple[str, str]]]]:
    """Decrypts the secrets file and returns the values of the specified keys.

    Args:
        payload (SecretsCatPayload): The payload detailing the keys to extract.

    Returns:
        ResultPayload[dict[Literal["values"], list[tuple[str, str]]]]: The result payload containing a list of values found for the keys.
    """
    import subprocess
    from io import StringIO

    from chaos.lib.secret_backends.crypto import is_vault_in_use
    from chaos.lib.secret_backends.utils import _handle_provider_arg, get_sops_files

    context = payload.context
    secretsFile, sopsFile, global_config = get_sops_files(
        context.sops_file_override, context.secrets_file_override, context.team
    )

    context = _handle_provider_arg(context, global_config)

    errors = []
    messages = []

    if not secretsFile or not sopsFile:
        errors.append(
            "SOPS check requires both secrets file and sops config file paths.\n"
            "       Configure them using 'chaos -sec' and 'chaos -sops', or pass them with '-sf' and '-ss'."
        )
        return ResultPayload(success=False, error=errors)

    if is_vault_in_use(sopsFile):
        from chaos.lib.secret_backends.crypto import check_vault_auth

        is_authed, message = check_vault_auth()
        if not is_authed:
            errors.append(message)
            return ResultPayload(success=False, error=errors)

    try:
        sopsDecryptResult = None
        if payload.cat_sops_file:
            sopsDecryptResult = subprocess.run(
                ["cat", sopsFile], check=True, text=True, capture_output=True
            ).stdout
        else:
            from .secret_backends.utils import decrypt_secrets

            decrypt_result = decrypt_secrets(
                secretsFile, sopsFile, global_config, context
            )

            if not decrypt_result.data:
                errors.append("Decryption failed. No output received.")
                return ResultPayload(success=False, message=messages, error=errors)

            if not decrypt_result.success:
                errors.extend(decrypt_result.error)
                return ResultPayload(success=False, message=messages, error=errors)

            sopsDecryptResult = decrypt_result.data

        if sopsDecryptResult is None:
            errors.append("SOPS decryption result is None. This should not happen.")
            return ResultPayload(success=False, message=messages, error=errors)

        from omegaconf import OmegaConf

        ocLoadResult = OmegaConf.load(StringIO(sopsDecryptResult))
        values: list[tuple[str, str]] = []
        for key in payload.keys:
            value = OmegaConf.select(ocLoadResult, key, default=None)
            if value is None:
                messages.append(f"{key} not found in {secretsFile}.")
                continue

            values.append((key, value))
        return ResultPayload(
            success=True, message=messages, error=errors, data={"values": values}
        )

    except subprocess.CalledProcessError as e:
        details = e.stderr if e.stderr else "No output."
        errors.append(f"SOPS decryption failed.\nDetails: {details}")
        return ResultPayload(success=False, message=messages, error=errors)
    except FileNotFoundError:
        errors.append(
            "'sops' command not found. Please ensure sops is installed and in your PATH."
        )
        return ResultPayload(success=False, message=messages, error=errors)


def handleExportSec(
    payload: SecretsExportPayload, global_config: DictConfig
) -> ResultPayload[Any]:
    """Exports secrets via a resolved provider.

    Args:
        payload (SecretsExportPayload): The payload details for the export.
        global_config (dict | DictConfig): The global configuration.

    Returns:
        ResultPayload: The result payload of the export operation.
    """
    from chaos.lib.secret_backends.utils import _getProviderByName

    provider = _getProviderByName(payload, global_config)
    return provider.export_secrets(payload)


def handleImportSec(payload: SecretsImportPayload, global_config) -> ResultPayload:
    """Imports secrets via a resolved provider.

    Args:
        payload (SecretsImportPayload): The payload details for the import.
        global_config (dict | DictConfig): The global configuration.

    Returns:
        ResultPayload: The result payload of the import operation.
    """
    from chaos.lib.secret_backends.utils import _getProviderByName

    provider = _getProviderByName(payload, global_config)
    return provider.import_secrets(payload)
