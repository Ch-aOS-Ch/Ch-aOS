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
def printCheck(namespace, dispatcher):
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

    title = f"[italic][green]Available [/][bold blue]{namespace}s[/][/]:"
    render_list_as_table(list(dispatcher.keys()), title)

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


def checkRoles(ROLES_DISPATCHER, **kwargs):
    printCheck("role", ROLES_DISPATCHER)

def checkExplanations(EXPLANATIONS, **kwargs):
    printCheck("explanation", EXPLANATIONS)

def checkAliases(ROLE_ALIASES, **kwargs):
    printCheck("alias", ROLE_ALIASES)

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
        import hvac
        client = hvac.Client(url=vault_addr, token=vault_token)
        if client.is_authenticated():
            return True, "[green]INFO:[/] Vault token is valid."
        else:
            return False, "[bold red]ERROR:[/] Vault token is invalid or expired. Please log in to Vault."
    except ImportError:
        return False, "[bold red]ERROR:[/] The 'hvac' library is not installed. Please install it to use Vault features (`pip install hvac`)."
    except Exception as e:
        return False, f"[bold red]ERROR:[/] Failed to authenticate with Vault at {vault_addr}: {e}"
