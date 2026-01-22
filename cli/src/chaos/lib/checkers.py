import os
from typing import cast
from chaos.lib.utils import render_list_as_table


"""
Handles listing of roles/explanations/aliases with rich rendering.

+ some validity checks for vault
"""

"""
Handles the printing of the lists.
"""
def printCheck(namespace, dispatcher, json_output=False):
    if not json_output:
        from rich.console import Console
        from rich.panel import Panel
        from rich.table import Table
        from rich.align import Align
        console = Console()
        if not dispatcher:
            console.print(f"[bold red][italic]No {namespace}s found.[/][/]")
            return

        if namespace == 'alias':
            dispatcher = _handleAliases(dispatcher)

            table = Table(show_lines=True)
            table.add_column("[green]Alias[/]", justify="center")
            table.add_column("[green]Maps to[/]", justify="center")
            for p, r in dispatcher.items():
                table.add_row(f"[cyan][italic]{p}[/][/]", f"[italic][cyan]{r}[/][/]")
            console.print(Align.center(Panel(table, border_style="green", expand=False, title=f"[italic][green]Available [/][bold blue]{namespace}es[/][/]:")))
            return

        title = f"[italic][green]Available [/][bold blue]{namespace}s[/][/]"
        if namespace == 'secret':
            render_list_as_table(dispatcher, title)
            return
        render_list_as_table(list(dispatcher.keys()), title)
    else:
        import json
        if namespace == 'secret':
            print (json.dumps(dispatcher, indent=2))
            return
        print(json.dumps(list(dispatcher.keys()), indent=2))

def _handleAliases(dispatcher):
    from rich.console import Console
    from omegaconf import DictConfig, OmegaConf
    console = Console()
    CONFIG_DIR = os.path.expanduser("~/.config/chaos")
    CONFIG_FILE_PATH = os.path.join(CONFIG_DIR, "config.yml")
    global_config = OmegaConf.create()
    if os.path.exists(CONFIG_FILE_PATH):
        global_config = OmegaConf.load(CONFIG_FILE_PATH) or OmegaConf.create()
    global_config = cast(DictConfig, global_config)

    userAliases = global_config.get('aliases', {})
    for a in userAliases.keys():
        if a in dispatcher:
            console.print(f"[bold yellow]WARNING:[/] Alias {a} already exists in Aliases installed. Skipping.")
            del userAliases[a]

    dispatcher.update(userAliases)
    return dispatcher

def flatten_dict_keys(d, parent_key='', sep='.'):
    """
    """
    items = []
    for k, v in d.items():
        new_key = f"{parent_key}{sep}{k}" if parent_key else k

        if new_key == 'sops':
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

"""
checks if vault is in use in the sops file
yeah, just that
"""
def is_vault_in_use(sops_file_path: str) -> bool:
    from omegaconf import DictConfig, OmegaConf
    if not sops_file_path or not os.path.exists(sops_file_path):
        return False
    try:
        config = OmegaConf.load(sops_file_path)
        config = cast(DictConfig, config)
        creation_rules = config.get('creation_rules', [])
        for rule in creation_rules:
            for key_group in rule.get('key_groups', []):
                if 'vault' in key_group and key_group.get('vault'):
                    return True
    except Exception:
        return False
    return False

"""checks if vault auth is valid"""
def check_vault_auth():
    vault_addr = os.getenv('VAULT_ADDR')
    if not vault_addr:
        return False, "[bold red]ERROR:[/] VAULT_ADDR environment variable is not set, which is required when using Vault keys."

    vault_token = os.getenv('VAULT_TOKEN')
    if not vault_token:
        return False, "[bold red]ERROR:[/] VAULT_TOKEN environment variable is not set. Please log in to Vault."

    try:
        import hvac # type: ignore
        client = hvac.Client(url=vault_addr, token=vault_token)
        if client.is_authenticated():
            return True, "[green]INFO:[/] Vault token is valid."
        else:
            return False, "[bold red]ERROR:[/] Vault token is invalid or expired. Please log in to Vault."
    except ImportError:
        return False, "[bold red]ERROR:[/] The 'hvac' library is not installed. Please install it to use Vault features (`pip install hvac`)."
    except Exception as e:
        return False, f"[bold red]ERROR:[/] Failed to authenticate with Vault at {vault_addr}: {e}"
