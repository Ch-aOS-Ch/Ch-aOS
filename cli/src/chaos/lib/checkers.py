import os
from typing import cast

from .args.dataclasses import CheckPayload

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

        if namespace == "alias":
            dispatcher = _handleAliases(dispatcher)

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
                        title=f"[italic][green]Available [/][bold blue]{namespace}es[/][/]:",
                    )
                )
            )

            return

        title = f"[italic][green]Available [/][bold blue]{namespace}s[/][/]"
        if namespace == "secret":
            from chaos.lib.display_utils import render_list_as_table

            render_list_as_table(dispatcher, title)
            return
        from chaos.lib.display_utils import render_list_as_table

        render_list_as_table(list(dispatcher.keys()), title)
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


def checkSecrets(secrets_file, isJson=False):
    from omegaconf import OmegaConf

    secrets_dict = OmegaConf.to_container(OmegaConf.load(secrets_file), resolve=True)
    flat_secrets = flatten_dict_keys(secrets_dict)
    printCheck("secret", flat_secrets, json_output=isJson)


def checkRoles(ROLES_DISPATCHER, isJson=False):
    printCheck("role", ROLES_DISPATCHER, json_output=isJson)


def checkExplanations(EXPLANATIONS, isJson=False):
    printCheck("explanation", EXPLANATIONS, json_output=isJson)


def checkAliases(ROLE_ALIASES, isJson=False):
    printCheck("alias", ROLE_ALIASES, json_output=isJson)


def checkProviders(providers, isJson=False):
    printCheck("provider", providers, json_output=isJson)


def checkBoats(boats, isJson=False):
    printCheck("boat", boats, json_output=isJson)


def checkLimanis(limanis, isJson=False):
    printCheck("limani", limanis, json_output=isJson)


def checkTemplates(keys, isJson=False):
    printCheck("template", keys, json_output=isJson)


def is_vault_in_use(sops_file_path: str) -> bool:
    """
    checks if vault is in use in the sops file
    yeah, just that
    """
    from omegaconf import DictConfig, OmegaConf

    if not sops_file_path or not os.path.exists(sops_file_path):
        return False
    try:
        config = OmegaConf.load(sops_file_path)
        config = cast(DictConfig, config)
        creation_rules = config.get("creation_rules", [])
        for rule in creation_rules:
            for key_group in rule.get("key_groups", []):
                if "vault" in key_group and key_group.get("vault"):
                    return True
    except Exception:
        return False
    return False


def check_vault_auth():
    """checks if vault auth is valid"""
    vault_addr = os.getenv("VAULT_ADDR")
    if not vault_addr:
        return (
            False,
            "[bold red]ERROR:[/] VAULT_ADDR environment variable is not set, which is required when using Vault keys.",
        )

    vault_token = os.getenv("VAULT_TOKEN")
    if not vault_token:
        return (
            False,
            "[bold red]ERROR:[/] VAULT_TOKEN environment variable is not set. Please log in to Vault.",
        )

    try:
        from hvac import Client

        client = Client(url=vault_addr, token=vault_token)
        if client.is_authenticated():
            return True, "[green]INFO:[/] Vault token is valid."
        else:
            return (
                False,
                "[bold red]ERROR:[/] Vault token is invalid or expired. Please log in to Vault.",
            )
    except ImportError:
        return (
            False,
            "[bold red]ERROR:[/] The 'hvac' library is not installed. Please install it to use Vault features (`pip install hvac`).",
        )
    except Exception as e:
        return (
            False,
            f"[bold red]ERROR:[/] Failed to authenticate with Vault at {vault_addr}: {e}",
        )


def handle_check(payload: CheckPayload):
    import sys

    match payload.checks:
        case "explanations":
            from chaos.lib.plugDiscovery import get_plugins

            EXPLANATIONS = get_plugins(payload.update_plugins)[2]
            checkExplanations(EXPLANATIONS, payload.json)
        case "aliases":
            from chaos.lib.plugDiscovery import get_plugins

            ROLE_ALIASES = get_plugins(payload.update_plugins)[1]
            checkAliases(ROLE_ALIASES, payload.json)
        case "roles":
            from chaos.lib.plugDiscovery import get_plugins

            role_specs = get_plugins(payload.update_plugins)[0]
            checkRoles(role_specs, payload.json)
        case "providers":
            from chaos.lib.plugDiscovery import get_plugins

            providers = get_plugins(payload.update_plugins)[4]
            checkProviders(providers, payload.json)

        case "boats":
            from chaos.lib.plugDiscovery import get_plugins

            boats = get_plugins(payload.update_plugins)[5]
            checkBoats(boats)

        case "secrets":
            from chaos.lib.checkers import checkSecrets
            from chaos.lib.secret_backends.utils import get_sops_files

            sec_file = get_sops_files(
                payload.sops_file_override,
                payload.secrets_file_override,
                payload.team,
            )[0]
            checkSecrets(sec_file, payload.json)

        case "limanis":
            from chaos.lib.plugDiscovery import get_plugins

            limanis = get_plugins(payload.update_plugins)[6]
            checkLimanis(limanis, payload.json)

        case "templates":
            from chaos.lib.plugDiscovery import get_plugins

            keys = get_plugins(payload.update_plugins)[3]
            checkTemplates(keys, payload.json)

        case _:
            print(
                "No valid checks passed, valid checks: explain, alias, roles, secrets"
            )

    sys.exit(0)
