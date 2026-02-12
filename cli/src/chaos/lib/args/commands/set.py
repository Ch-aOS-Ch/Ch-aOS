import sys


def handleSet(args):
    from rich.console import Console

    console = Console()
    from chaos.lib.handlers import setMode

    is_setter_mode = any(
        [
            hasattr(args, "chobolo_file") and args.chobolo_file,
            hasattr(args, "secrets_file") and args.secrets_file,
            hasattr(args, "sops_file") and args.sops_file,
        ]
    )
    if is_setter_mode:
        from chaos.lib.args.dataclasses import SetPayload

        payload = SetPayload(
            chobolo_file=getattr(args, "chobolo_file", None),
            secrets_file=getattr(args, "secrets_file", None),
            sops_file=getattr(args, "sops_file", None),
        )

        try:
            setMode(payload)
        except FileNotFoundError as e:
            console.print(f"[bold red]ERROR:[/] {e}")
            sys.exit(1)
        sys.exit(0)
