import sys


def handleApply(args):
    from rich.console import Console

    console = Console()
    from typing import cast

    from omegaconf import DictConfig
    from pyinfra.api import exceptions as pyinfra_exceptions  # type: ignore

    from chaos.lib.args.dataclasses import (
        ApplyPayload,
        ProviderConfigPayload,
        SecretsContext,
    )
    from chaos.lib.handlers import handleOrchestration
    from chaos.lib.plugDiscovery import load_roles
    from chaos.lib.utils import get_providerEps

    """
    The apply command needs some special handling, as it is the main entry point for OS orchestration.
    We load the roles, handle verbosity, and then pass control to the orchestration handler.
    """
    try:
        from chaos.lib.plugDiscovery import get_plugins

        role_specs, ROLE_ALIASES = get_plugins(args.update_plugins)[0:2]
        ROLES_DISPATCHER = load_roles(role_specs)

        provider_eps = get_providerEps()
        provider_classes = [ep.load() for ep in provider_eps] if provider_eps else []

        ephemeral_provider_args = {}
        for provider_class in provider_classes:
            flag_name, _ = provider_class.get_cli_name()
            if flag_name and hasattr(args, flag_name):
                value = getattr(args, flag_name, None)
                if value:
                    ephemeral_provider_args[flag_name] = value

        provider_config = ProviderConfigPayload(
            provider=getattr(args, "provider", None),
            ephemeral_provider_args=ephemeral_provider_args,
        )

        secrets_context = SecretsContext(
            team=getattr(args, "team", None),
            sops_file_override=getattr(args, "sops_file", None),
            secrets_file_override=getattr(args, "secrets_file", None),
            provider_config=provider_config,
            i_know_what_im_doing=getattr(args, "i_know_what_im_doing", False),
        )

        payload = ApplyPayload(
            update_plugins=args.update_plugins,
            i_know_what_im_doing=args.i_know_what_im_doing,
            dry=args.dry,
            verbose=args.verbose,
            v=args.v,
            tags=getattr(args, "tags", []),
            chobolo=getattr(args, "chobolo", None),
            limani=getattr(args, "limani", None),
            logbook=getattr(args, "logbook", False),
            fleet=getattr(args, "fleet", False),
            sudo_password_file=getattr(args, "sudo_password_file", None),
            password=getattr(args, "password", None),
            secrets=getattr(args, "secrets", False),
            serial=getattr(args, "serial", False),
            no_wait=getattr(args, "no_wait", False),
            export_logs=getattr(args, "export_logs", False),
            secrets_context=secrets_context,
        )

        if payload.tags:
            ROLES_DISPATCHER = cast(DictConfig, ROLES_DISPATCHER)
            ROLE_ALIASES = cast(DictConfig, ROLE_ALIASES)

            handleOrchestration(payload, ROLES_DISPATCHER, ROLE_ALIASES)
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
