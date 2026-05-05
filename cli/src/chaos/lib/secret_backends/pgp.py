import subprocess
from typing import TYPE_CHECKING, cast

from omegaconf import DictConfig, OmegaConf

from chaos.lib.secret_backends.utils import (
    _generic_handle_add,
    _generic_handle_rem,
    flatten,
)

from .crypto import is_valid_fp, pgp_exists

if TYPE_CHECKING:
    from chaos.lib.args.dataclasses import SecretsRotatePayload


"""
GPG specific handlers for add/rem/list
"""


def listPgp(
    sops_file_override: str,
) -> tuple[set[str], list[str], list[str], list[str]]:
    """Lists all PGP key fingerprints found in the given SOPS configuration file.

    Args:
        sops_file_override (str): The path to the SOPS configuration file.

    Returns:
        tuple[set[str], list[str], list[str], list[str]]: A tuple containing:
            - A set of all found PGP key fingerprints.
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

        all_pgp_keys_in_config = set()
        for rule in creation_rules:
            for key_group in rule.get("key_groups", []):
                if "pgp" in key_group and key_group.pgp is not None:
                    all_pgp_keys_in_config.update(flatten(key_group.pgp))

        if not all_pgp_keys_in_config:
            messages.append("No keys to be shown.")
            warnings.append("No keys to be shown.")

        return all_pgp_keys_in_config, warnings, error, messages

    except Exception as e:
        error.append(f"Failed to read sops config file: {e}")
        messages.append(f"Failed to read sops config file: {e}")
        return set(), warnings, error, messages


def handlePgpAdd(
    payload: SecretsRotatePayload, sops_file_override: str, keys: list[str]
) -> tuple[list[str], list[str]]:
    """Handles the addition of PGP key fingerprints to the SOPS configuration.

    Validates fingerprints, ensures they exist locally (fetching from a keyserver if specified),
    and adds them to the configuration.

    Args:
        payload (SecretsRotatePayload): The payload containing rotation options and pgp_server.
        sops_file_override (str): The path to the SOPS configuration file.
        keys (list[str]): The list of PGP key fingerprints to add.

    Returns:
        tuple[list[str], list[str]]: A tuple containing a list of informational messages
            and a list of error messages.
    """
    server = payload.pgp_server
    valids = set()
    errors = []
    messages = []
    for key in keys:
        clean_key = key.replace(" ", "")
        if len(clean_key) < 40:
            errors.append(f"Unsafe PGP key fingerprint: {key}. Skipping.")
            errors.append(
                "To list your GPG keys, run: gpg --list-secret-keys --keyid-format LONG"
            )
            continue

        if not is_valid_fp(clean_key):
            errors.append(f"Invalid PGP fingerprint: {key}. Skipping.")
            errors.append(
                "To list your GPG keys, run: gpg --list-secret-keys --keyid-format LONG"
            )
            continue

        if not pgp_exists(clean_key):
            errors.append(f"PGP fingerprint {key} does not exist locally.")
            if not server:
                errors.append(
                    f"PGP fingerprint {key} does not exist locally and no server was passed. Skipping"
                )
                errors.append(
                    "To list your GPG keys, run: gpg --list-secret-keys --keyid-format LONG"
                )
                continue
            try:
                command_message = subprocess.run(
                    ["gpg", "--keyserver", server, "--recv-keys", clean_key],
                    check=True,
                    capture_output=True,
                    text=True,
                ).stdout
                messages.append(command_message)
                messages.append(
                    f"Fingerprint {key} was successfully imported from {server}"
                )
            except subprocess.SubprocessError as e:
                errors.append(f"Could not import {key} from {server}: {e}.\nSkipping.")
                continue
        valids.add(clean_key)
    msgs, errs = _generic_handle_add("pgp", payload, sops_file_override, valids)
    messages.extend(msgs)
    errors.extend(errs)
    return messages, errors


def handlePgpRem(
    payload: SecretsRotatePayload, sops_file_override: str, keys: list[str]
) -> tuple[list[str], list[str]]:
    """Handles the removal of PGP key fingerprints from the SOPS configuration.

    Args:
        payload (SecretsRotatePayload): The payload containing rotation context.
        sops_file_override (str): The path to the SOPS configuration file.
        keys (list[str]): The list of PGP key fingerprints to remove.

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

        all_pgp_keys_in_config = set()
        for rule in creation_rules:
            for key_group in rule.get("key_groups", []):
                if "pgp" in key_group and key_group.pgp is not None:
                    all_pgp_keys_in_config.update(flatten(key_group.pgp))

        keys_to_remove = set()
        for key_to_check in keys:
            clean_key = key_to_check.replace(" ", "")
            if not is_valid_fp(clean_key):
                errors.append(f"Invalid PGP fingerprint: {key_to_check}. Skipping.")
                continue

            if clean_key in all_pgp_keys_in_config:
                keys_to_remove.add(clean_key)
            else:
                messages.append(
                    f"Fingerprint: {key_to_check} not found in sops config. Skipping."
                )
        msgs, errs = _generic_handle_rem(
            "pgp", payload, sops_file_override, keys_to_remove
        )
        messages.extend(msgs)
        errors.extend(errs)

    except Exception as e:
        errors.append(f"Failed to update sops config file: {e}")
    return messages, errors
