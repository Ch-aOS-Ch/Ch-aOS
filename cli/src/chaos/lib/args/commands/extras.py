import sys

from ..args import handleGenerateTab


def handle_(args):
    from rich.console import Console

    console = Console()
    if args.generate_tab:
        handleGenerateTab()
        sys.exit(0)

    elif args.edit_chobolo:
        try:
            from chaos.lib.tinyScript import runChoboloEdit

            runChoboloEdit(args.chobolo)
        except (ValueError, FileNotFoundError, RuntimeError) as e:
            console.print(f"[bold red]ERROR:[/] {e}")
            sys.exit(1)

    elif args.update_plugins:
        try:
            from chaos.lib.plugDiscovery import get_plugins

            get_plugins(update_cache=True)
            console.print("[bold green]Plugins updated successfully.[/]")
            sys.exit(0)
        except (RuntimeError, EnvironmentError) as e:
            console.print(f"[bold red]ERROR:[/] {e}")
            sys.exit(1)
