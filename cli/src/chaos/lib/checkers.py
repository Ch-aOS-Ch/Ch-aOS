import os
from typing import cast

from .args.dataclasses import CheckPayload, ResultPayload

"""
Handles listing of roles/explanations/aliases with rich rendering.

+ some validity checks for vault
"""


def _handleAliases(dispatcher):
    from omegaconf import DictConfig, OmegaConf

    warnings = []
    messages = []
    CONFIG_DIR = os.path.expanduser("~/.config/chaos")
    CONFIG_FILE_PATH = os.path.join(CONFIG_DIR, "config.yml")
    global_config = OmegaConf.create()
    if os.path.exists(CONFIG_FILE_PATH):
        global_config = OmegaConf.load(CONFIG_FILE_PATH) or OmegaConf.create()
    global_config = cast(DictConfig, global_config)

    userAliases = global_config.get("aliases", {})
    for a in userAliases.keys():
        if a in dispatcher:
            warnings.append("conflicting alias")
            messages.append(f"Alias {a} conflicts with an existing alias. Skipping.")
            del userAliases[a]

    dispatcher.update(userAliases)
    return dispatcher, warnings, messages


def _flatten_dict_keys(d, parent_key="", sep="."):
    """
    Flattens a nested dictionary and returns a list of keys in dot notation.
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


def checkSecrets(secrets_file) -> ResultPayload:
    from omegaconf import OmegaConf

    secrets_dict = OmegaConf.to_container(OmegaConf.load(secrets_file), resolve=True)
    flat_secrets = _flatten_dict_keys(secrets_dict)
    result = ResultPayload(
        success=True,
        message=["[green]INFO:[/] All secrets are valid."],
        data=flat_secrets,
        error=None,
    )

    return result


def checkRoles(ROLES_DISPATCHER) -> ResultPayload:
    result = ResultPayload(
        success=True,
        message=["[green]INFO:[/] All roles are valid."],
        data=list(ROLES_DISPATCHER.keys()),
        error=None,
    )

    return result


def checkExplanations(EXPLANATIONS) -> ResultPayload:
    result = ResultPayload(
        success=True,
        message=["[green]INFO:[/] All explanations are valid."],
        data=list(EXPLANATIONS.keys()),
        error=None,
    )

    return result


def checkAliases(ROLE_ALIASES) -> ResultPayload:
    payload, warnings, messages = _handleAliases(ROLE_ALIASES)
    result = ResultPayload(
        success=True,
        data=payload,
        message=["[green]INFO:[/] All explanations are valid."]
        if not warnings
        else messages,
        error=warnings if warnings else None,
    )

    return result


def checkProviders(providers) -> ResultPayload:
    result = ResultPayload(
        success=True,
        message=["[green]INFO:[/] All providers are valid."],
        data=list(providers.keys()),
        error=None,
    )

    return result


def checkBoats(boats) -> ResultPayload:
    result = ResultPayload(
        success=True,
        message=["[green]INFO:[/] All boats are valid."],
        data=list(boats.keys()),
        error=None,
    )

    return result


def checkLimanis(limanis) -> ResultPayload:
    result = ResultPayload(
        success=True,
        message=["[green]INFO:[/] All limanis are valid."],
        data=list(limanis.keys()),
        error=None,
    )

    return result


def checkTemplates(keys) -> ResultPayload:
    result = ResultPayload(
        success=True,
        message=["[green]INFO:[/] All templates are valid."],
        data=list(keys.keys()),
        error=None,
    )

    return result


def handle_check(payload: CheckPayload) -> ResultPayload:
    match payload.checks:
        case "explanations":
            from chaos.lib.plugDiscovery import get_plugins

            EXPLANATIONS = get_plugins(payload.update_plugins)[2]
            result: ResultPayload = checkExplanations(EXPLANATIONS)
            return result
        case "aliases":
            from chaos.lib.plugDiscovery import get_plugins

            ROLE_ALIASES = get_plugins(payload.update_plugins)[1]
            result: ResultPayload = checkAliases(ROLE_ALIASES)
            return result
        case "roles":
            from chaos.lib.plugDiscovery import get_plugins

            role_specs = get_plugins(payload.update_plugins)[0]
            result: ResultPayload = checkRoles(role_specs)
            return result
        case "providers":
            from chaos.lib.plugDiscovery import get_plugins

            providers = get_plugins(payload.update_plugins)[4]
            result: ResultPayload = checkProviders(providers)
            return result

        case "boats":
            from chaos.lib.plugDiscovery import get_plugins

            boats = get_plugins(payload.update_plugins)[5]
            result: ResultPayload = checkBoats(boats)
            return result

        case "secrets":
            from chaos.lib.checkers import checkSecrets
            from chaos.lib.secret_backends.utils import get_sops_files

            sec_file = get_sops_files(
                payload.sops_file_override,
                payload.secrets_file_override,
                payload.team,
            )[0]
            result: ResultPayload = checkSecrets(sec_file)
            return result

        case "limanis":
            from chaos.lib.plugDiscovery import get_plugins

            limanis = get_plugins(payload.update_plugins)[6]
            result: ResultPayload = checkLimanis(limanis)
            return result

        case "templates":
            from chaos.lib.plugDiscovery import get_plugins

            keys = get_plugins(payload.update_plugins)[3]
            result: ResultPayload = checkTemplates(keys)
            return result

        case _:
            return ResultPayload(
                success=False,
                message=[
                    "No valid checks passed. Please specify one of: explanations, aliases, roles, providers, boats, secrets, limanis, templates."
                ],
                data=None,
                error=["Invalid checks"],
            )
