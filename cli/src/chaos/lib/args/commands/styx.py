import sys


def handleStyx(args):
    from rich.console import Console

    console = Console()
    try:
        match args.styx_commands:
            case "invoke":
                from chaos.lib.styx import install_styx_entries

                entries: list[str] = args.entries
                install_styx_entries(entries)

            case "list":
                from chaos.lib.styx import list_styx_entries

                entries: list[str] = args.entries
                listing: list[str] | str = list_styx_entries(
                    entries, args.no_pretty, args.json
                )

                if args.no_pretty:
                    print(listing)
                else:
                    console.print(listing)

            case "destroy":
                from chaos.lib.styx import uninstall_styx_entries

                entries: list[str] = args.entries
                uninstall_styx_entries(entries)
            case _:
                console.print("Unsupported styx subcommand.")
    except (ValueError, FileNotFoundError, RuntimeError, EnvironmentError) as e:
        console.print(f"[bold red]ERROR:[/] {e}")
        sys.exit(1)
