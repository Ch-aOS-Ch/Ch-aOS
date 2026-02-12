import sys


# TODO: add payload
def handleApply(args):
    from rich.console import Console

    console = Console()
    from typing import cast

    from omegaconf import DictConfig
    from pyinfra.api import exceptions as pyinfra_exceptions  # type: ignore

    from chaos.lib.handlers import handleOrchestration, handleVerbose
    from chaos.lib.plugDiscovery import load_roles

    """
    The apply command needs some special handling, as it is the main entry point for OS orchestration.
    We load the roles, handle verbosity, and then pass control to the orchestration handler.
    """
    try:
        from chaos.lib.plugDiscovery import get_plugins

        role_specs, ROLE_ALIASES = get_plugins(args.update_plugins)[0:2]
        ROLES_DISPATCHER = load_roles(role_specs)
        ikwid = args.i_know_what_im_doing
        dry = args.dry
        if args.verbose or args.v > 0:
            handleVerbose(args)

        if args.tags:
            ROLES_DISPATCHER = cast(DictConfig, ROLES_DISPATCHER)
            ROLE_ALIASES = cast(DictConfig, ROLE_ALIASES)

            handleOrchestration(args, dry, ikwid, ROLES_DISPATCHER, ROLE_ALIASES)
        else:
            print("No tags passed.")
    except FileNotFoundError as e:
        console.print(f"[bold red]ERROR:[/] {e}")
        sys.exit(1)

    except pyinfra_exceptions.PyinfraError as e:
        print(f"Unexpected pyinfra error: {e}", file=sys.stderr)
        sys.exit(1)

    except (RuntimeError, ValueError) as e:
        console.print(f"[bold red]ERROR:[/] {e}")
        sys.exit(1)
