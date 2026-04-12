from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from chaos.lib.args.dataclasses import Delta


def handleApply(args):
    import sys

    from rich.console import Console

    console = Console()

    from chaos.lib.apply import (
        execute_plans,
        gather_apply,
        gather_fleet,
        get_configs,
        resolve_aliases,
        run_delta,
        run_filtered_context,
        run_plan,
        setup_pyinfra,
        teardown_pyinfra,
    )
    from chaos.lib.args.dataclasses import (
        ApplyPayload,
        ProviderConfigPayload,
        SecretsContext,
    )
    from chaos.lib.roles.role import Role

    ikwid = getattr(args, "i_know_what_im_doing", False)

    sudo_pass = ""
    if not sys.stdin.isatty():
        console.print(
            "[bold yellow]WARNING:[/] No TTY detected. Reading sudo password from stdin. -y flag is implied."
        )
        sudo_pass = sys.stdin.read().strip()
        ikwid = True

    if args.password:
        sudo_pass = args.password

    if args.sudo_password_file:
        try:
            with open(args.sudo_password_file, "r") as f:
                sudo_pass = f.read().strip()
        except Exception as e:
            console.print(f"[bold red]ERROR:[/] Failed to read sudo password file: {e}")
            sys.exit(1)

    provider_config = ProviderConfigPayload(
        provider=getattr(args, "provider", None),
        ephemeral_provider_args=None,
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

    _handle_verbose(payload)

    global_config, config_result = get_configs(payload)
    _print_messages(config_result, console)

    from typing import cast

    from omegaconf import OmegaConf

    container = OmegaConf.to_container(global_config, resolve=False)
    payload.global_config = cast(dict[str, Any], container)

    alias_result = resolve_aliases(payload)
    _print_messages(alias_result, console)
    if alias_result.success:
        if alias_result.data:
            payload.tags = alias_result.data

    apply_request, apply_result = gather_apply(payload)

    if apply_result.data is None:
        console.print("[bold red]ERROR:[/] No data returned from apply orchestration.")
        sys.exit(1)

    prompt = None
    confirm = None
    prompt, confirm = _handle_apply_prompts(
        apply_request,
        payload,
        console,
        prompt,
        confirm,
        apply_result.data.get("any_role_needs_secrets", False),
    )
    _check_and_exit_on_error(apply_result, console, "apply orchestration")

    if payload.secrets:
        from chaos.lib.utils import get_providerEps

        provider_eps = get_providerEps()
        provider_classes = [ep.load() for ep in provider_eps] if provider_eps else []

        ephemeral_provider_args = {}
        for provider_class in provider_classes:
            flag_name, _ = provider_class.get_cli_name()
            if flag_name and hasattr(args, flag_name):
                value = getattr(args, flag_name, None)
                if value:
                    ephemeral_provider_args[flag_name] = value

        provider_config.ephemeral_provider_args = ephemeral_provider_args

    if not isinstance(apply_result.data, dict):
        console.print(
            "[bold red]ERROR:[/] Apply orchestration returned invalid data format."
        )
        sys.exit(1)

    if not apply_result.data:
        console.print("[bold red]ERROR:[/] Apply orchestration returned empty data.")
        sys.exit(1)

    if not apply_result.data.get("global_config"):
        console.print("[bold red]ERROR:[/] Global config is missing from apply result.")
        sys.exit(1)

    if not config_result.data or not config_result.data.get("chobolo_path"):
        console.print("[bold red]ERROR:[/] Chobolo path is missing from config result.")
        sys.exit(1)

    if not apply_result.data.get("loaded_roles"):
        console.print("[bold red]ERROR:[/] Loaded roles are missing from apply result.")
        sys.exit(1)

    payload.global_config = apply_result.data["global_config"]
    payload.chobolo = config_result.data["chobolo_path"]
    payload.secrets_context.secrets_file_override = config_result.data[
        "secrets_file_override"
    ]
    payload.secrets_context.sops_file_override = config_result.data[
        "sops_file_override"
    ]

    loaded_roles: dict[str, Role] = apply_result.data["loaded_roles"]

    chobolo_config_oc = (
        OmegaConf.load(payload.chobolo) if payload.chobolo else OmegaConf.create()
    )

    fleet_request, fleet_result = gather_fleet(
        payload, chobolo_config_oc, payload.chobolo
    )

    confirm = _handle_fleet_prompts(fleet_request, console, confirm)
    _check_and_exit_on_error(fleet_result, console, "fleet orchestration")

    if fleet_result.data:
        payload.target_hosts = fleet_result.data.get("hosts", ["@local"])
        payload.is_fleet_active = fleet_result.data.get("is_fleet", False)
        payload.parallelism = fleet_result.data.get("parallels", 0)

    run_status = "success"
    try:
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
                raw_container = OmegaConf.to_container(
                    OmegaConf.create(secrets), resolve=False
                )

                payload.decrypted_secrets = cast(dict[str, Any], raw_container)
            except Exception as e:
                console.print(f"[bold red]ERROR:[/] Failed to decrypt secrets: {e}")
                sys.exit(1)

        chobolo_config = OmegaConf.to_container(chobolo_config_oc, resolve=False)
        chobolo_config = cast(dict[str, Any], chobolo_config)

        restrictions = chobolo_config.get("restrictions", {})

        roles = list(loaded_roles.values())
        hosts = list(payload.pyinfra_state.inventory.iter_activated_hosts())

        console.print("[bold blue]INFO:[/] Collecting host contexts...")

        if payload.pyinfra_state.pool:
            from functools import partial

            gathered_results = payload.pyinfra_state.pool.map(
                partial(
                    run_filtered_context,
                    roles=roles,
                    payload=payload,
                    chobolo_config=chobolo_config,
                    restrictions=restrictions,
                ),
                hosts,
            )
        else:
            gathered_results = [
                run_filtered_context(h, roles, payload, chobolo_config, restrictions)
                for h in hosts
            ]

        has_changes_to_apply = False
        prepared_plans = []

        for host_result in gathered_results:
            if not host_result.success:
                _print_messages(host_result, console)
                run_status = "failure"
                continue
            if not host_result.data:
                console.print(
                    "[bold red]ERROR:[/] No data returned from host context gathering."
                )
                run_status = "failure"
                continue
            host = host_result.data["host"]

            for role_name, data in host_result.data["roles"].items():
                role = data["role"]
                context = data["context"]

                delta_result = run_delta(context, role, role_name)
                _print_messages(delta_result, console)
                if not delta_result.success:
                    run_status = "failure"
                    continue

                if delta_result.data is None:
                    console.print(
                        f"[bold red]ERROR:[/] No delta data returned for role {role.name} on host {host.name}."
                    )
                    run_status = "failure"
                    continue

                delta: Delta = delta_result.data
                _render_delta(delta, role_name, host.name, console)

                if delta.to_add or delta.to_remove:
                    has_changes_to_apply = True
                    prepared_plans.append((delta, role, role_name, host))
                else:
                    console.print(
                        f"[bold green]NOOP:[/] Role '{role.name}' on host '{host.name}' is already in the desired state."
                    )

        if has_changes_to_apply and not payload.i_know_what_im_doing:
            if sys.stdin.isatty():
                if not prompt or not confirm:
                    from rich.prompt import Confirm, Prompt

                    prompt = Prompt()
                    confirm = Confirm()

                if not confirm.ask(
                    "\n[bold yellow]Do you wish to apply the above deltas?[/]",
                    default=True,
                ):
                    console.print("[bold red]Aborting apply due to user response.[/]")
                    sys.exit(1)

        for delta, role, role_name, host in prepared_plans:
            plan_result = run_plan(payload, delta, role, role_name, host)
            _print_messages(plan_result, console)
            if not plan_result.success:
                run_status = "failure"

        if has_changes_to_apply or payload.i_know_what_im_doing:
            console.print("[bold blue]INFO:[/] Executing apply plans...")
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
        teardown_result = teardown_pyinfra(payload, run_status)
        _check_and_exit_on_error(teardown_result, console, "teardown pyinfra")


def _handle_verbose(payload) -> None:
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


def _handle_apply_prompts(
    request, payload, console, prompt, confirm, any_role_needs_secrets
):
    """Handles the interactive data gathering for the apply phase."""
    import sys

    if not request:
        return prompt, confirm

    if not sys.stdin.isatty():
        console.print(
            "[bold yellow]WARNING:[/] No TTY detected. Skipping interactive prompts. If you need to provide secrets, please run the command in an interactive terminal."
        )
        return prompt, confirm

    if not prompt or not confirm:
        from rich.prompt import Confirm, Prompt

        confirm = Confirm()
        prompt = Prompt()

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
                if any_role_needs_secrets:
                    payload.secrets = True
    return prompt, confirm


def _handle_fleet_prompts(request, console, confirm):
    """Handles the interactive data gathering for the fleet phase."""
    import sys

    if not request:
        return confirm

    if sys.stdin.isatty():
        if not confirm:
            from rich.prompt import Confirm

            confirm = Confirm()

        for field in request.fields:
            if field.input_type == "boolean":
                if field.prompt:
                    confirmation = confirm.ask(field.prompt, default=field.default)
                    if not confirmation:
                        console.print(
                            "[bold red]Aborting apply due to user response.[/]"
                        )
                        sys.exit(1)


def _render_delta(
    delta,
    role_name,
    host_name,
    console,
):
    """Renders the proposed changes (delta) to the console."""
    to_add = delta.to_add
    to_remove = delta.to_remove

    if not (to_add or to_remove):
        return

    console.print(
        f"[bold blue]INFO:[/] Role [bold]'{role_name}'[/] on host: '{host_name}' has the following delta:"
    )

    if to_add:
        for item, details in to_add.items():
            if details:
                console.print(f"  ----- To add: {item} -----")
                to_add_string = "".join(f"    + {detail}\n" for detail in details)
                console.print(f"[green]{to_add_string}[/]")

    if to_remove:
        for item, details in to_remove.items():
            if details:
                console.print(f"  ----- To remove: {item} -----")
                to_remove_string = "".join(f"    - {detail}\n" for detail in details)
                console.print(f"[red]{to_remove_string}[/]")
