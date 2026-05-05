from typing import cast

from omegaconf import DictConfig, OmegaConf

from chaos.lib.secret_backends.utils import (
    _generic_handle_add,
    _generic_handle_rem,
    _is_valid_vault_key,
    flatten,
)

"""
Vault specific handlers for add/rem/list
"""


def listVault(
    sops_file_override: str,
) -> tuple[set[str], list[str], list[str], list[str]]:
    """Lists all Vault instances/URIs found in the given SOPS configuration file.

    Args:
        sops_file_override (str): The path to the SOPS configuration file.

    Returns:
        tuple[set[str], list[str], list[str], list[str]]: A tuple containing:
            - A set of all found Vault URIs.
            - A list of warning messages.
            - A list of error messages.
            - A list of informational messages.
    """
    warnings = []
    error = []
    messages = []
    try:
        sops_config = OmegaConf.load(sops_file_override)
        sops_config = cast(DictConfig, sops_config)
        creation_rules = sops_config.get("creation_rules")
        if not creation_rules:
            messages.append(
                "No 'creation_rules' found in the sops config. Nothing to do."
            )
            error.append("No 'creation_rules' found in the sops config. Nothing to do.")
            return set(), warnings, error, messages

        all_vault_keys_in_config = set()
        for rule in creation_rules:
            for key_group in rule.get("key_groups", []):
                if "vault" in key_group and key_group.vault is not None:
                    all_vault_keys_in_config.update(flatten(key_group.vault))

        if not all_vault_keys_in_config:
            messages.append("No keys to be shown.")
            warnings.append("No keys to be shown.")

        return all_vault_keys_in_config, warnings, error, messages

    except Exception as e:
        error.append(f"Failed to read sops config file: {e}")
        messages.append(f"Failed to read sops config file: {e}")
        return set(), warnings, error, messages


def handleVaultAdd(payload, sops_file_override, keys):
    """Handles the addition of Vault URIs to the SOPS configuration.

    Validates Vault URIs connectivity/format and updates the configuration.

    Args:
        payload (SecretsRotatePayload): The payload containing rotation options.
        sops_file_override (str): The path to the SOPS configuration file.
        keys (list[str]): The list of Vault URIs to add.

    Returns:
        tuple[list[str], list[str]]: A tuple containing a list of informational messages
            and a list of error messages.
    """
    messages = []
    errors = []
    valids = set()
    for key in keys:
        clean_key = key.strip()
        is_valid, message = _is_valid_vault_key(clean_key)
        if is_valid:
            messages.append(message)
            valids.add(clean_key)
        else:
            errors.append(f"{message} Skipping key '{key}'.")
            continue

    msgs, errs = _generic_handle_add("vault", payload, sops_file_override, valids)
    messages.extend(msgs)
    errors.extend(errs)
    return messages, errors


def handleVaultRem(payload, sops_file_override, keys):
    """Handles the removal of Vault URIs from the SOPS configuration.

    Args:
        payload (SecretsRotatePayload): The payload containing rotation context.
        sops_file_override (str): The path to the SOPS configuration file.
        keys (list[str]): The list of Vault URIs to remove.

    Returns:
        tuple[list[str], list[str]]: A tuple containing a list of informational messages
            and a list of error messages.
    """
    messages = []
    errors = []
    try:
        config_data = OmegaConf.load(sops_file_override)
        config_data = cast(DictConfig, config_data)
        creation_rules = config_data.get("creation_rules", [])
        if not creation_rules:
            errors.append(
                "No 'creation_rules' found in the sops config. Nothing to do."
            )
            return messages, errors

        all_vault_keys_in_config = set()
        for rule in creation_rules:
            for key_group in rule.get("key_groups", []):
                if "vault" in key_group and key_group.vault is not None:
                    all_vault_keys_in_config.update(flatten(key_group.vault))

        keys_to_remove = set()
        for key_to_check in keys:
            clean_key = key_to_check.strip()

            if clean_key in all_vault_keys_in_config:
                keys_to_remove.add(clean_key)
            else:
                messages.append(
                    f"Key: {key_to_check} not found in sops config. Skipping."
                )

        msgs, errs = _generic_handle_rem(
            "vault", payload, sops_file_override, keys_to_remove
        )
        messages.extend(msgs)
        errors.extend(errs)

    except Exception as e:
        errors.append(f"Failed to update sops config file: {e}")
    return messages, errors
