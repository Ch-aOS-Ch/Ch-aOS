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


def _print_messages(result, console):
    """Helper to print warnings and errors from a ResultPayload."""
    import sys

    if result.success:
        return
    for message in result.message:
        console.print(f"[bold yellow]WARNING:[/] {message}")

    for error in result.error:
        console.print(f"[bold red]ERROR:[/] {error}")
    sys.exit(1)


def _check_and_exit_on_error(result, console, stage_name="orchestration"):
    """Checks a result, prints its messages, and exits if it failed."""
    import sys

    if not result:
        console.print(f"[bold red]ERROR:[/] No valid result from {stage_name}.")
        sys.exit(1)

    _print_messages(result, console)

    if not result.success:
        sys.exit(1)


def _handle_apply_prompts(request, payload, console, prompt, confirm):
    """Handles the interactive data gathering for the apply phase."""
    import sys

    if not request:
        return

    if not sys.stdin.isatty():
        console.print(
            "[bold yellow]WARNING:[/] No TTY detected. Skipping interactive prompts. If you need to provide secrets, please run the command in an interactive terminal."
        )
        return

    for field in request.fields:
        if field.input_type == "secret":
            if field.prompt:
                value = prompt.ask(field.prompt, password=True)
                payload.password = value

        if field.input_type == "boolean":
            if field.prompt:
                confirmation = confirm.ask(field.prompt, default=field.default)
                if not confirmation:
                    console.print("[bold red]Aborting apply due to user response.[/]")
                    sys.exit(1)
                payload.secrets = True


def _handle_fleet_prompts(request, console, confirm):
    """Handles the interactive data gathering for the fleet phase."""
    import sys

    if not request:
        return

    for field in request.fields:
        if field.input_type == "boolean":
            if field.prompt:
                confirmation = confirm.ask(field.prompt, default=field.default)
                if not confirmation:
                    console.print("[bold red]Aborting apply due to user response.[/]")
                    sys.exit(1)


def _render_delta(
    delta,
    role_name,
    host_name,
    ikwid,
    console,
):
    """Renders the proposed changes (delta) to the console."""
    to_add = delta.to_add
    to_remove = delta.to_remove

    if not (to_add or to_remove) or ikwid:
        return

    console.print(
        f"[bold blue]INFO:[/] Role [bold]{role_name}[/] on host: {host_name} has the following delta:"
    )

    if to_add:
        for item, details in to_add.items():
            if details:
                console.print(f"  ----- To add: {item} -----")
                for detail in details:
                    console.print(f"    [green]+ {detail}[/]")

    if to_remove:
        for item, details in to_remove.items():
            if details:
                console.print(f"  ----- To remove: {item} -----")
                for detail in details:
                    console.print(f"    [red]- {detail}[/]")


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
    _print_messages(alias_result, console)
    if alias_result.success:
        payload.tags = alias_result.data

    from chaos.lib.apply import gather_apply

    apply_request, apply_result = gather_apply(payload)

    _handle_apply_prompts(apply_request, payload, console, prompt, confirm)
    _check_and_exit_on_error(apply_result, console, "apply orchestration")

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

    _handle_fleet_prompts(fleet_request, console, confirm)
    _check_and_exit_on_error(fleet_result, console, "fleet orchestration")

    try:
        run_status = "success"
        from chaos.lib.apply import setup_pyinfra

        setup_result = setup_pyinfra(payload)
        _check_and_exit_on_error(setup_result, console, "setup pyinfra")

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
                    _print_messages(allowlist_blacklist_result, console)
                    if not allowlist_blacklist_result.success:
                        sys.exit(1)
                    continue

                context_result = run_context(payload, role, host)
                _print_messages(context_result, console)
                if not context_result.success:
                    run_status = "failure"
                    continue

                context = context_result.data

                delta_result = run_delta(context, role, role.name)
                _print_messages(delta_result, console)
                if not delta_result.success:
                    run_status = "failure"
                    continue

                delta: Delta = delta_result.data

                _render_delta(
                    delta, role.name, host.name, payload.i_know_what_im_doing, console
                )

                if (
                    delta.to_add or delta.to_remove
                ) and not payload.i_know_what_im_doing:
                    if not confirm.ask(
                        "Do you want to apply this change?", default=True
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
                _print_messages(plan_result, console)
                if not plan_result.success:
                    run_status = "failure"
                    continue

        from chaos.lib.apply import execute_plans

        execute_result = execute_plans(payload)
        _print_messages(execute_result, console)
        if not execute_result.success:
            run_status = "failure"
            console.print("[bold red]Apply execution completed with errors.[/]")
            sys.exit(1)

    except Exception as e:
        console.print(f"[bold red]ERROR:[/] Failed to import pyinfra: {e}")
        run_status = "failure"

    finally:
        from chaos.lib.apply import teardown_pyinfra

        teardown_result = teardown_pyinfra(payload, run_status)
        _check_and_exit_on_error(teardown_result, console, "teardown pyinfra")
