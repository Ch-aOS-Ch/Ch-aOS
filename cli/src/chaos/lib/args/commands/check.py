from chaos.lib.args.dataclasses import ResultPayload


def _printCheck(namespace, dispatcher, json_output=False):
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


def handleCheck(args):
    from chaos.lib.args.dataclasses import CheckPayload
    from chaos.lib.checkers import handle_check

    payload = CheckPayload(
        checks=args.checks,
        chobolo=getattr(args, "chobolo", None),
        json=getattr(args, "json", False),
        team=getattr(args, "team", None),
        sops_file_override=getattr(args, "sops_file_override", None),
        secrets_file_override=getattr(args, "secrets_file_override", None),
        update_plugins=getattr(args, "update_plugins", False),
    )

    result: ResultPayload = handle_check(payload)

    if result.error:
        from rich.console import Console

        console = Console()
        if not result.success:
            for error in result.message:
                console.print(f"[bold red][italic]Error:[/] {error}[/]")
            return

        for error in result.message:
            console.print(f"[bold yellow]WARNING:[/] {error}[/]")

    if result.success:
        _printCheck(payload.checks, result.data, json_output=payload.json)
