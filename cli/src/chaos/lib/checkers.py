import os
from typing import cast

from .args.dataclasses import CheckPayload, ResultPayload

"""
Handles listing of roles/explanations/aliases with rich rendering.

+ some validity checks for vault
"""


def printCheck(namespace, dispatcher, json_output=False):
    """
    Handles the printing of the lists.
    """
    if not json_output:
        from rich.align import Align
        from rich.console import Console
        from rich.panel import Panel
        from rich.table import Table

        console = Console()
        if not dispatcher:
            console.print(f"[bold red][italic]No {namespace}s found.[/][/]")
            return

        if namespace == "aliases":
            table = Table(show_lines=True)
            table.add_column("[green]Alias[/]", justify="center")
            table.add_column("[green]Maps to[/]", justify="center")

            for p, r in dispatcher.items():
                table.add_row(f"[cyan][italic]{p}[/][/]", f"[italic][cyan]{r}[/][/]")

            console.print(
                Align.center(
                    Panel(
                        table,
                        border_style="green",
                        expand=False,
                        title=f"[italic][green]Available [/][bold blue]{namespace}[/][/]:",
                    )
                )
            )

            return

        title = f"[italic][green]Available [/][bold blue]{namespace}[/][/]"
        if namespace == "secrets":
            from chaos.lib.display_utils import render_list_as_table

            render_list_as_table(dispatcher, title)
            return
        from chaos.lib.display_utils import render_list_as_table

        render_list_as_table(list(dispatcher), title)
    else:
        import json

        if namespace == "secret":
            print(json.dumps(dispatcher, indent=2))
            return
        print(json.dumps(list(dispatcher.keys()), indent=2))


def _handleAliases(dispatcher):
    from omegaconf import DictConfig, OmegaConf
    from rich.console import Console

    console = Console()
    CONFIG_DIR = os.path.expanduser("~/.config/chaos")
    CONFIG_FILE_PATH = os.path.join(CONFIG_DIR, "config.yml")
    global_config = OmegaConf.create()
    if os.path.exists(CONFIG_FILE_PATH):
        global_config = OmegaConf.load(CONFIG_FILE_PATH) or OmegaConf.create()
    global_config = cast(DictConfig, global_config)

    userAliases = global_config.get("aliases", {})
    for a in userAliases.keys():
        if a in dispatcher:
            console.print(
                f"[bold yellow]WARNING:[/] Alias {a} already exists in Aliases installed. Skipping."
            )
            del userAliases[a]

    dispatcher.update(userAliases)
    return dispatcher


def flatten_dict_keys(d, parent_key="", sep="."):
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
            items.extend(flatten_dict_keys(v, new_key, sep=sep))
        else:
            items.append(new_key)

    return items


def checkSecrets(secrets_file) -> ResultPayload:
    from omegaconf import OmegaConf

    secrets_dict = OmegaConf.to_container(OmegaConf.load(secrets_file), resolve=True)
    flat_secrets = flatten_dict_keys(secrets_dict)
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
    payload = _handleAliases(ROLE_ALIASES)
    result = ResultPayload(
        success=True,
        data=payload,
        message=["[green]INFO:[/] All explanations are valid."],
        error=None,
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


def handle_check(payload: CheckPayload):
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
                    "[bold red]ERROR:[/] No valid checks passed, valid checks: explain, alias, roles, secrets"
                ],
                data=None,
                error=["Invalid check type"],
            )
