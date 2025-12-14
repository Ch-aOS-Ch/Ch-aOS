import math
from itertools import zip_longest
from typing import cast

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from omegaconf import OmegaConf, DictConfig
import os

console = Console()

def printCheck(namespace, dispatcher):
    if not dispatcher:
        console.print(f"[bold red][italic]No {namespace}s found.[/][/]")
        return

    if namespace == 'alias':
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

        if dispatcher:
            dispatcher.update(userAliases)

        table = Table(show_lines=True)
        table.add_column("[green]Alias[/]", justify="center")
        table.add_column("[green]Maps to[/]", justify="center")
        for p, r in dispatcher.items():
            table.add_row(f"[cyan][italic]{p}[/][/]", f"[italic][cyan]{r}[/][/]")
        console.print(Panel(table, border_style="green", expand=False, title=f"[italic][green]Available [/][bold blue]{namespace}es[/][/]:"))
        return

    items = sorted(list(dispatcher))
    num_items = len(items)
    max_rows = 4

    if num_items < 5:
        table = Table(show_lines=True)
        table.add_column()
        for item in items:
            table.add_row(f"[italic][cyan]{item}[/][/]")
        console.print(Panel(table, border_style="green", expand=False, title=f"[italic][green]Available [/][bold blue]{namespace}s:[/][/]"))
    else:
        num_columns = math.ceil(num_items / max_rows)
        table = Table(
            show_lines=True,
            expand=False,
            show_header=False
        )

        for _ in range(num_columns):
            table.add_column(justify="center")

        chunks = [items[i:i + max_rows] for i in range(0, num_items, max_rows)]
        transposed_items = zip_longest(*chunks, fillvalue="")

        for row_data in transposed_items:
            styled_row = [f"[cyan][italic]{item}[/][/]" if item else "" for item in row_data]
            table.add_row(*styled_row)

        console.print(Panel(table, border_style="green", expand=False, title=f"[italic][green]Available [/][bold blue]{namespace}s[/][/]:"))


def checkRoles(ROLES_DISPATCHER, **kwargs):
    printCheck("role", ROLES_DISPATCHER)

def checkExplanations(EXPLANATIONS, **kwargs):
    printCheck("explanation", EXPLANATIONS)

def checkAliases(ROLE_ALIASES, **kwargs):
    printCheck("alias", ROLE_ALIASES)
