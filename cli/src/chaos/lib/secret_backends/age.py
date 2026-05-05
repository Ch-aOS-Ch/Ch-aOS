from typing import TYPE_CHECKING, cast

from omegaconf import DictConfig, OmegaConf

from chaos.lib.secret_backends.utils import (
    _generic_handle_add,
    _generic_handle_rem,
    flatten,
)

from .crypto import is_valid_age_key

if TYPE_CHECKING:
    from chaos.lib.args.dataclasses import SecretsRotatePayload

"""
AGE specific handlers for add/rem/list
"""


def listAge(
    sops_file_override: str,
) -> tuple[set[str], list[str], list[str], list[str]]:
    """Lists all Age public keys found in the given SOPS configuration file.

    Args:
        sops_file_override (str): The path to the SOPS configuration file.

    Returns:
        tuple[set[str], list[str], list[str], list[str]]: A tuple containing:
            - A set of all found Age public keys.
            - A list of warning messages.
            - A list of error messages.
            - A list of informational messages.
    """
    warnings: list[str] = []
    error: list[str] = []
    messages: list[str] = []
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

        all_age_keys_in_config = set()
        for rule in creation_rules:
            for key_group in rule.get("key_groups", []):
                if "age" in key_group and key_group.age is not None:
                    all_age_keys_in_config.update(flatten(key_group.age))

        if not all_age_keys_in_config:
            messages.append("No keys to be shown.")
            warnings.append("No keys to be shown.")

        return all_age_keys_in_config, warnings, error, messages

    except Exception as e:
        error.append(f"Failed to read sops config file: {e}")
        messages.append(f"Failed to read sops config file: {e}")
        return set(), warnings, error, messages


def handleAgeAdd(
    payload: SecretsRotatePayload, sops_file_override: str, keys: list[str]
):
    """Handles the addition of Age public keys to the SOPS configuration.

    Validates Age keys and then updates the configuration with valid ones.

    Args:
        payload (SecretsRotatePayload): The payload containing rotation options.
        sops_file_override (str): The path to the SOPS configuration file.
        keys (list[str]): The list of Age public keys to add.

    Returns:
        tuple[list[str], list[str]]: A tuple containing a list of informational messages
            and a list of error messages.
    """
    valids = set()
    messages = []
    errors = []
    for key in keys:
        clean_key = key.strip()
        if not is_valid_age_key(clean_key):
            errors.append(f"Invalid age key: {key}. Skipping.")
            errors.append("To get your age public key:")
            errors.append(
                "  - From a native age private key file (e.g., ~/.config/chaos/keys.txt): age-keygen -y ~/.config/chaos/keys.txt"
            )
            errors.append(
                "  - From a SSH public key (e.g., ~/.ssh/id_rsa.pub, requires ssh-to-age): ssh-to-age -i ~/.ssh/id_rsa.pub"
            )
            continue
        valids.add(clean_key)

    msgs, errs = _generic_handle_add("age", payload, sops_file_override, valids)
    messages.extend(msgs)
    errors.extend(errs)
    return messages, errors


def handleAgeRem(
    payload: SecretsRotatePayload, sops_file_override: str, keys: list[str]
):
    """Handles the removal of Age public keys from the SOPS configuration.

    Args:
        payload (SecretsRotatePayload): The payload containing rotation context.
        sops_file_override (str): The path to the SOPS configuration file.
        keys (list[str]): The list of Age public keys to remove.

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

        all_age_keys_in_config = set()
        for rule in creation_rules:
            for key_group in rule.get("key_groups", []):
                if "age" in key_group and key_group.age is not None:
                    all_age_keys_in_config.update(flatten(key_group.age))

        keys_to_remove = set()
        for key_to_check in keys:
            clean_key = key_to_check.strip()

            if clean_key in all_age_keys_in_config:
                keys_to_remove.add(clean_key)
            else:
                messages.append(
                    f"Key: {key_to_check} not found in sops config. Skipping."
                )

        msgs, errs = _generic_handle_rem(
            "age", payload, sops_file_override, keys_to_remove
        )
        messages.extend(msgs)
        errors.extend(errs)

    except Exception as e:
        errors.append(f"Failed to update sops config file: {e}")
    return messages, errors
