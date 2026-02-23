import sys


def handleRamble(args):
    from rich.console import Console

    console = Console()
    try:
        from ...utils import get_providerEps
        from ..dataclasses import (
            ProviderConfigPayload,
            RambleCreatePayload,
            RambleDeletePayload,
            RambleEditPayload,
            RambleEncryptPayload,
            RambleFindPayload,
            RambleMovePayload,
            RambleReadPayload,
            RambleUpdateEncryptPayload,
            SecretsContext,
        )

        team = getattr(args, "team", None)
        sops_file_override = getattr(args, "sops_file_override", None)

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

        ramble_context = SecretsContext(
            team=team,
            sops_file_override=sops_file_override,
            secrets_file_override=None,
            provider_config=provider_config,
            i_know_what_im_doing=False,
        )

        match args.ramble_commands:
            case "create":
                from ...ramble import handleCreateRamble

                payload = RambleCreatePayload(
                    target=args.target,
                    encrypt=getattr(args, "encrypt", False),
                    keys=getattr(args, "keys", None),
                    context=ramble_context,
                )

                handleCreateRamble(payload)
            case "edit":
                from ...ramble import handleEditRamble

                payload = RambleEditPayload(
                    target=args.target,
                    edit_sops_file=getattr(args, "sops", False),
                    context=ramble_context,
                )

                handleEditRamble(payload)
            case "encrypt":
                from ...ramble import handleEncryptRamble

                payload = RambleEncryptPayload(
                    target=args.target,
                    keys=getattr(args, "keys", None),
                    context=ramble_context,
                )

                handleEncryptRamble(payload)
            case "read":
                from ...ramble import handleReadRamble

                payload = RambleReadPayload(
                    targets=args.targets,
                    no_pretty=getattr(args, "no_pretty", False),
                    json=getattr(args, "json", False),
                    values=getattr(args, "values", None),
                    context=ramble_context,
                )

                handleReadRamble(payload)
            case "find":
                from ...ramble import handleFindRamble

                payload = RambleFindPayload(
                    find_term=getattr(args, "find_term", None),
                    tag=getattr(args, "tag", None),
                    no_pretty=getattr(args, "no_pretty", False),
                    json=getattr(args, "json", False),
                    context=ramble_context,
                )

                result = handleFindRamble(payload)

                if result.message:
                    for msg in result.message:
                        console.print(f"[cyan]INFO:[/] {msg}")

                if result.error:
                    for err in result.error:
                        console.print(f"[bold yellow]WARNING:[/] {err}")

                if result.success and result.data:
                    from omegaconf import OmegaConf

                    results = result.data
                    if payload.no_pretty:
                        if payload.json:
                            import json as js

                            print(
                                js.dumps(
                                    OmegaConf.to_container(
                                        OmegaConf.create(results), resolve=True
                                    ),
                                    indent=2,
                                )
                            )
                        else:
                            print(OmegaConf.to_yaml(OmegaConf.create(results)))
                    else:
                        from chaos.lib.display_utils import render_list_as_table

                        title = "[italic][green]Found ramblings:[/][/]"
                        render_list_as_table(results, title)
                elif not result.error:
                    console.print("[yellow]Could not find any rambles.[/]")
            case "move":
                from ...ramble import handleMoveRamble

                payload = RambleMovePayload(
                    old=args.old,
                    new=args.new,
                    context=ramble_context,
                )

                handleMoveRamble(payload)
            case "delete":
                from ...ramble import handleDelRamble

                payload = RambleDeletePayload(
                    ramble=args.ramble,
                    context=ramble_context,
                )

                handleDelRamble(payload)
            case "update":
                from ...ramble import handleUpdateEncryptRamble

                payload = RambleUpdateEncryptPayload(
                    context=ramble_context,
                )

                handleUpdateEncryptRamble(payload)
            case _:
                console.print("Unsupported ramble subcommand.")
    except (
        ValueError,
        FileNotFoundError,
        PermissionError,
        RuntimeError,
        FileExistsError,
    ) as e:
        console.print(f"[bold red]ERROR:[/] {e}")
        sys.exit(1)
