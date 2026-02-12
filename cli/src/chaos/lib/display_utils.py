import math
from itertools import zip_longest

from rich.align import Align
from rich.console import Console
from rich.panel import Panel
from rich.table import Table


def render_list_as_table(items: list[str], panel_title: str):
    """Renders a list of strings into a responsive multi-column table using rich."""
    console = Console()
    if not items:
        console.print("[bold yellow]No items found.[/]")
        return

    sorted_items = sorted(list(set(items)))
    num_items = len(sorted_items)
    max_rows = 4

    if num_items < 5:
        table = Table(show_lines=True, expand=False, show_header=False)
        table.add_column(justify="center")
        for item in sorted_items:
            table.add_row(f"[italic][cyan]{item}[/][/]")
    else:
        num_columns = math.ceil(num_items / max_rows)
        table = Table(show_lines=True, expand=False, show_header=False)
        for _ in range(num_columns):
            table.add_column(justify="center")

        chunks = [sorted_items[i : i + max_rows] for i in range(0, num_items, max_rows)]
        transposed_items = zip_longest(*chunks, fillvalue="")

        for row_data in transposed_items:
            styled_row = [
                f"[cyan][italic]{item}[/][/]" if item else "" for item in row_data
            ]
            table.add_row(*styled_row)

    console.print(
        Align.center(
            Panel(
                Align.center(table),
                border_style="green",
                expand=False,
                title=panel_title,
            )
        ),
        justify="center",
    )
