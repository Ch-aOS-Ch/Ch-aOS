"""Handles listing of roles/explanations/aliases with rich rendering.

Notes:
    + some validity checks for vault
"""

from __future__ import annotations

import os
from typing import Any, cast

from .args.dataclasses import CheckPayload, ResultPayload


def _handleAliases(
    dispatcher: dict[str, str],
) -> tuple[dict[str, str], list[str], list[str]]:
    """Handles aliases by merging user aliases with the dispatcher.

    Args:
        dispatcher (dict): The dictionary of existing aliases.

    Returns:
        tuple[dict, list[str], list[str]]: A tuple containing the updated dispatcher, a list of warnings, and a list of messages.
    """
    from pathlib import Path

    from omegaconf import DictConfig, OmegaConf

    warnings = []
    messages = []
    CONFIG_DIR = os.getenv("CHAOS_CONFIG_DIR", Path.home() / ".config" / "chaos")
    CONFIG_FILE_PATH = os.path.join(CONFIG_DIR, "config.yml")
    global_config = OmegaConf.create()
    if os.path.exists(CONFIG_FILE_PATH):
        global_config = OmegaConf.load(CONFIG_FILE_PATH) or OmegaConf.create()
    global_config = cast(DictConfig, global_config)

    userAliases = global_config.get("aliases", {})
    for a in list(userAliases.keys()):
        if a in dispatcher:
            warnings.append("conflicting alias")
            messages.append(f"Alias {a} conflicts with an existing alias. Skipping.")
            del userAliases[a]

    dispatcher.update(userAliases)
    return dispatcher, warnings, messages


def _flatten_dict_keys(
    d: dict[str, Any], parent_key: str = "", sep: str = "."
) -> list[str]:
    """Flattens a nested dictionary and returns a list of keys in dot notation.

    Args:
        d (dict): The dictionary to flatten.
        parent_key (str, optional): The base key to use for nested elements. Defaults to "".
        sep (str, optional): The separator to use between keys. Defaults to ".".

    Returns:
        list[str]: A list of keys in dot notation.

    Notes:
        Skips the 'sops' key during the flattening process and appends it at the end if it exists.
    """
    items = []
    for k, v in d.items():
        new_key = f"{parent_key}{sep}{k}" if parent_key else k

        if k == "sops":
            items.append(new_key)
            continue

        if isinstance(v, dict) and v:
            items.extend(_flatten_dict_keys(v, new_key, sep=sep))
        else:
            items.append(new_key)

    return items


def checkSecrets(secrets_file: str) -> ResultPayload[list[str]]:
    """Checks if the secrets in the specified file are valid.

    Args:
        secrets_file (str): The path to the secrets file.

    Returns:
        ResultPayload[list[str]]: The result payload containing a list of flattened secrets keys if successful.
    """

    from omegaconf import OmegaConf

    secrets_dict = cast(
        dict[str, Any],
        OmegaConf.to_container(OmegaConf.load(secrets_file), resolve=True),
    )

    flat_secrets = _flatten_dict_keys(secrets_dict)
    result = ResultPayload(
        success=True,
        message=["All secrets are valid"],
        data=flat_secrets,
        error=None,
    )

    return result


def checkRoles(ROLES_DISPATCHER: dict[str, str]) -> ResultPayload[list[str]]:
    """Checks if the provided roles are valid.

    Args:
        ROLES_DISPATCHER (dict): A dictionary of roles to check.

    Returns:
        ResultPayload[list[str]]: The result payload containing a list of valid roles.
    """
    result = ResultPayload(
        success=True,
        message=["All roles are valid"],
        data=list(ROLES_DISPATCHER.keys()),
        error=None,
    )

    return result


def checkExplanations(EXPLANATIONS: dict[str, str]) -> ResultPayload[list[str]]:
    """Checks if the provided explanations are valid.

    Args:
        EXPLANATIONS (dict): A dictionary of explanations to check.

    Returns:
        ResultPayload[list[str]]: The result payload containing a list of valid explanations.
    """
    result = ResultPayload(
        success=True,
        message=["All explanations are valid"],
        data=list(EXPLANATIONS.keys()),
        error=None,
    )

    return result


def checkAliases(ROLE_ALIASES: dict[str, str]) -> ResultPayload[dict[str, str]]:
    """Checks if the provided aliases are valid.

    Args:
        ROLE_ALIASES (dict): A dictionary of role aliases to check.

    Returns:
        ResultPayload[dict[str, str]]: The result payload containing the valid aliases, and any warnings/messages.
    """
    payload, warnings, messages = _handleAliases(ROLE_ALIASES)
    result = ResultPayload(
        success=True,
        data=payload,
        message=["All explanations are valid"] if not warnings else messages,
        error=warnings if warnings else None,
    )

    return result


def checkProviders(providers: dict[str, str]) -> ResultPayload[list[str]]:
    """Checks if the provided providers are valid.

    Args:
        providers (dict): A dictionary of providers to check.

    Returns:
        ResultPayload[list[str]]: The result payload containing a list of valid providers.
    """
    result = ResultPayload(
        success=True,
        message=["All providers are valid"],
        data=list(providers.keys()),
        error=None,
    )

    return result


def checkBoats(boats: dict[str, str]) -> ResultPayload[list[str]]:
    """Checks if the provided boats are valid.

    Args:
        boats (dict): A dictionary of boats to check.

    Returns:
        ResultPayload[list[str]]: The result payload containing a list of valid boats.
    """
    result = ResultPayload(
        success=True,
        message=["All boats are valid"],
        data=list(boats.keys()),
        error=None,
    )

    return result


def checkLimanis(limanis: dict[str, str]) -> ResultPayload[list[str]]:
    """Checks if the provided limanis are valid.

    Args:
        limanis (dict): A dictionary of limanis to check.

    Returns:
        ResultPayload[list[str]]: The result payload containing a list of valid limanis.
    """
    result = ResultPayload(
        success=True,
        message=["All limanis are valid"],
        data=list(limanis.keys()),
        error=None,
    )

    return result


def checkTemplates(keys: dict[str, str]) -> ResultPayload[list[str]]:
    """Checks if the provided templates are valid.

    Args:
        keys (dict): A dictionary of templates to check.

    Returns:
        ResultPayload[list[str]]: The result payload containing a list of valid templates.
    """
    result = ResultPayload(
        success=True,
        message=["All templates are valid"],
        data=list(keys.keys()),
        error=None,
    )

    return result


def handle_check(
    payload: CheckPayload,
) -> ResultPayload[list[str] | dict[str, str] | None]:
    """Handles various check commands based on the payload.

    Args:
        payload (CheckPayload): The payload containing the check command and related context.

    Returns:
        ResultPayload[list[str] | dict[str, str] | None]: The result payload of the requested check.
    """
    match payload.checks:
        case "explanations":
            from chaos.lib.plugDiscovery import get_plugins

            EXPLANATIONS = get_plugins(payload.update_plugins)[2]
            result_explain: ResultPayload[list[str]] = checkExplanations(EXPLANATIONS)
            return result_explain
        case "aliases":
            from chaos.lib.plugDiscovery import get_plugins

            ROLE_ALIASES = get_plugins(payload.update_plugins)[1]
            result_aliases: ResultPayload[dict[str, str]] = checkAliases(ROLE_ALIASES)
            return result_aliases
        case "roles":
            from chaos.lib.plugDiscovery import get_plugins

            role_specs = get_plugins(payload.update_plugins)[0]
            result_roles: ResultPayload[list[str]] = checkRoles(role_specs)
            return result_roles
        case "providers":
            from chaos.lib.plugDiscovery import get_plugins

            providers = get_plugins(payload.update_plugins)[4]
            result_providers: ResultPayload[list[str]] = checkProviders(providers)
            return result_providers

        case "boats":
            from chaos.lib.plugDiscovery import get_plugins

            boats = get_plugins(payload.update_plugins)[5]
            result_boats: ResultPayload[list[str]] = checkBoats(boats)
            return result_boats

        case "secrets":
            from chaos.lib.secret_backends.utils import get_sops_files

            sec_file = get_sops_files(
                payload.sops_file_override,
                payload.secrets_file_override,
                payload.team,
            )[0]
            result_secrets: ResultPayload[list[str]] = checkSecrets(sec_file)
            return result_secrets

        case "limanis":
            from chaos.lib.plugDiscovery import get_plugins

            limanis = get_plugins(payload.update_plugins)[6]
            result_limani: ResultPayload[list[str]] = checkLimanis(limanis)
            return result_limani

        case "templates":
            from chaos.lib.plugDiscovery import get_plugins

            keys = get_plugins(payload.update_plugins)[3]
            result_templates: ResultPayload[list[str]] = checkTemplates(keys)
            return result_templates

        case _:
            return ResultPayload(
                success=False,
                message=[
                    "No valid checks passed. Please specify one of: explanations, aliases, roles, providers, boats, secrets, limanis, templates."
                ],
                data=None,
                error=["Invalid checks"],
            )
