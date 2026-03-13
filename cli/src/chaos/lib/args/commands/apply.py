def handle_verbose(payload) -> None:
    """Handle verbosity levels for logging"""
    import logging

    log_level = None
    if payload.verbose:
        if payload.verbose == 1:
            log_level = logging.WARNING
        elif payload.verbose == 2:
            log_level = logging.INFO
        elif payload.verbose == 3:
            log_level = logging.DEBUG
    elif payload.v == 1:
        log_level = logging.WARNING
    elif payload.v == 2:
        log_level = logging.INFO
    elif payload.v == 3:
        log_level = logging.DEBUG

    if log_level:
        logging.basicConfig(level=log_level, format="%(levelname)s: %(message)s")


def handleApply(args):
    import sys
    from typing import TYPE_CHECKING

    from rich.console import Console
    from rich.prompt import Confirm, Prompt

    console = Console()
    prompt = Prompt()
    confirm = Confirm()

    from chaos.lib.utils import get_providerEps

    if TYPE_CHECKING:
        from chaos.lib.args.dataclasses import (
            ApplyPayload,
            Delta,
            ProviderConfigPayload,
            SecretsContext,
        )
        from chaos.lib.roles.role import Role

    ikwid = getattr(args, "i_know_what_im_doing", False)

    sudo_pass = ""
    if not sys.stdin.isatty():
        sudo_pass = sys.stdin.read().strip()
        ikwid = True

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
        i_know_what_im_doing=ikwid,
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
        password=sudo_pass,
        secrets=getattr(args, "secrets", False),
        serial=getattr(args, "serial", False),
        no_wait=getattr(args, "no_wait", False),
        export_logs=getattr(args, "export_logs", False),
        secrets_context=secrets_context,
    )

    handle_verbose(payload)

    from chaos.lib.apply import resolve_aliases

    alias_result = resolve_aliases(payload)
    if alias_result.success:
        for message in alias_result.message:
            console.print(f"[bold yellow]WARNING:[/] {message}")
        payload.tags = alias_result.data

    from chaos.lib.apply import gather_apply

    request_n_result = gather_apply(payload)
    apply_request = request_n_result[0]
    apply_result = request_n_result[1]

    if apply_request:
        if not sys.stdin.isatty():
            console.print(
                "[bold yellow]WARNING:[/] No TTY detected. Skipping interactive prompts. If you need to provide secrets, please run the command in an interactive terminal."
            )
        else:
            for field in apply_request.fields:
                if field.input_type == "secret":
                    if field.prompt:
                        value = prompt.ask(field.prompt, password=True)
                        payload.password = value
                if field.input_type == "boolean":
                    if field.prompt:
                        confirmation = confirm.ask(field.prompt, default=field.default)
                        if not confirmation:
                            console.print(
                                "[bold red]Aborting apply due to user response.[/]"
                            )
                            sys.exit(1)
                        payload.secrets = True

    if not apply_result:
        console.print("[bold red]ERROR:[/] No valid result from apply orchestration.")
        sys.exit(1)

    if not apply_result.success:
        for message in apply_result.message:
            console.print(f"[bold yellow]WARNING:[/] {message}")

        for error in apply_result.error:
            console.print(f"[bold red]ERROR:[/] {error}")

        sys.exit(1)

    payload.global_config = apply_result.data["global_config"]
    payload.chobolo = apply_result.data["chobolo_path"]
    payload.secrets_context.secrets_file_override = apply_result.data[
        "secrets_file_override"
    ]
    payload.secrets_context.sops_file_override = apply_result.data["sops_file_override"]

    loaded_roles: list[Role] = apply_result.data["loaded_roles"]

    from omegaconf import OmegaConf

    from chaos.lib.apply import gather_fleet

    chobolo_config = (
        OmegaConf.load(payload.chobolo) if payload.chobolo else OmegaConf.create()
    )

    fleet_request, fleet_result = gather_fleet(payload, chobolo_config, payload.chobolo)

    if fleet_request:
        for field in fleet_request.fields:
            if field.input_type == "boolean":
                if field.prompt:
                    confirmation = confirm.ask(field.prompt, default=field.default)
                    if not confirmation:
                        console.print(
                            "[bold red]Aborting apply due to user response.[/]"
                        )
                        sys.exit(1)

    if not fleet_result:
        console.print("[bold red]ERROR:[/] No valid result from fleet orchestration.")
        sys.exit(1)

    if not fleet_result.success:
        for message in fleet_result.message:
            console.print(f"[bold yellow]WARNING:[/] {message}")

        for error in fleet_result.error:
            console.print(f"[bold red]ERROR:[/] {error}")

        sys.exit(1)

    try:
        run_status = "success"
        from chaos.lib.apply import setup_pyinfra

        setup_result = setup_pyinfra(payload)
        if not setup_result.success:
            for message in setup_result.message:
                console.print(f"[bold yellow]WARNING:[/] {message}")

            for error in setup_result.error:
                console.print(f"[bold red]ERROR:[/] {error}")
            sys.exit(1)

        payload.pyinfra_state = setup_result.data

        if not payload.pyinfra_state:
            console.print("[bold red]ERROR:[/] Pyinfra state is missing after setup.")
            sys.exit(1)

        if payload.secrets:
            from chaos.lib.secret_backends.utils import decrypt_secrets

            try:
                secrets = decrypt_secrets(
                    payload.secrets_context.secrets_file_override,
                    payload.secrets_context.sops_file_override,
                    payload.global_config,
                    payload.secrets_context,
                )
                payload.decrypted_secrets = OmegaConf.create(secrets).to_container()
            except Exception as e:
                console.print(f"[bold red]ERROR:[/] Failed to decrypt secrets: {e}")
                sys.exit(1)

        from chaos.lib.apply import (
            resolve_allowlist_blacklist,
            run_context,
            run_delta,
            run_plan,
        )

        chobolo_config = chobolo_config.to_container()

        for host in payload.pyinfra_state.inventory.iter_activated_hosts():
            for role in loaded_roles:
                allowlist_blacklist_result = resolve_allowlist_blacklist(
                    chobolo_config.get("restrictions", {}), role.name, host
                )
                if allowlist_blacklist_result:
                    if not allowlist_blacklist_result.success:
                        for message in allowlist_blacklist_result.message:
                            console.print(f"[bold yellow]WARNING:[/] {message}")

                        for error in allowlist_blacklist_result.error:
                            console.print(f"[bold red]ERROR:[/] {error}")
                        sys.exit(1)
                    for message in allowlist_blacklist_result.message:
                        console.print(f"[bold yellow]WARNING:[/] {message}")
                    continue

                context_result = run_context(payload, role, host)
                if not context_result.success:
                    for message in context_result.message:
                        console.print(f"[bold yellow]WARNING:[/] {message}")

                    for error in context_result.error:
                        console.print(f"[bold red]ERROR:[/] {error}")
                    run_status = "failure"
                    continue

                context = context_result.data

                delta_result = run_delta(context, role, role.name)
                if not delta_result.success:
                    for message in delta_result.message:
                        console.print(f"[bold yellow]WARNING:[/] {message}")

                    for error in delta_result.error:
                        console.print(f"[bold red]ERROR:[/] {error}")
                    run_status = "failure"
                    continue

                delta: Delta = delta_result.data

                to_add = delta.to_add
                to_remove = delta.to_remove
                what_change = delta.is_changing

                if to_add or to_remove:
                    if not payload.i_know_what_im_doing:
                        console.print(
                            f"[bold blue]INFO:[/] Role [bold]{role.name}[/] on host: {host.name} has the following delta:"
                        )

                if to_add:
                    if not payload.i_know_what_im_doing:
                        console.print(f"  ----- {what_change} to add -----")
                        for item in to_add:
                            console.print(f"    [green]+ {item}[/]")

                if to_remove:
                    if not payload.i_know_what_im_doing:
                        console.print(f"  ----- {what_change} to remove -----")
                        for item in to_remove:
                            console.print(f"    [red]- {item}[/]")

                if (
                    not confirm.ask("Do you want to apply this change?", default=True)
                    and not payload.i_know_what_im_doing
                ):
                    if not confirm.ask(
                        "Do you want to try and apply these changes to other hosts?",
                        default=False,
                    ):
                        console.print(
                            "[bold red]Aborting apply due to user response.[/]"
                        )
                        sys.exit(1)
                    continue

                plan_result = run_plan(payload, delta, role, role.name, host)
                if not plan_result.success:
                    for message in plan_result.message:
                        console.print(f"[bold yellow]WARNING:[/] {message}")

                    for error in plan_result.error:
                        console.print(f"[bold red]ERROR:[/] {error}")
                    run_status = "failure"
                    continue

        from chaos.lib.apply import execute_plans

        execute_result = execute_plans(payload)
        if not execute_result.success:
            for message in execute_result.message:
                console.print(f"[bold yellow]WARNING:[/] {message}")
            for error in execute_result.error:
                console.print(f"[bold red]ERROR:[/] {error}")
            run_status = "failure"
            console.print("[bold red]Apply execution completed with errors.[/]")
            sys.exit(1)

    except Exception as e:
        console.print(f"[bold red]ERROR:[/] Failed to import pyinfra: {e}")
        run_status = "failure"

    finally:
        from chaos.lib.apply import teardown_pyinfra

        teardown_result = teardown_pyinfra(payload, run_status)
        if not teardown_result.success:
            for message in teardown_result.message:
                console.print(f"[bold yellow]WARNING:[/] {message}")

            for error in teardown_result.error:
                console.print(f"[bold red]ERROR:[/] {error}")
            sys.exit(1)
