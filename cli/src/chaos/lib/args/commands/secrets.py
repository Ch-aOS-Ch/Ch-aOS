import sys

from chaos.lib.args.dataclasses import ResultPayload


def handleSecrets(args):
    from rich.console import Console

    console = Console()
    try:
        from chaos.lib.args.dataclasses import (
            ProviderConfigPayload,
            SecretsCatPayload,
            SecretsContext,
            SecretsEditPayload,
            SecretsExportPayload,
            SecretsImportPayload,
            SecretsListPayload,
            SecretsPrintPayload,
            SecretsRotatePayload,
            SecretsSetShamirPayload,
        )
        from chaos.lib.secret_backends.utils import get_sops_files
        from chaos.lib.utils import get_providerEps

        team = getattr(args, "team", None)
        sops_file_override = getattr(args, "sops_file_override", None)
        secrets_file_override = getattr(args, "secrets_file_override", None)

        _, _, global_config = get_sops_files(
            sops_file_override, secrets_file_override, team
        )

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

        context = SecretsContext(
            team=team,
            sops_file_override=sops_file_override,
            secrets_file_override=secrets_file_override,
            provider_config=provider_config,
            i_know_what_im_doing=getattr(args, "i_know_what_im_doing", False),
        )

        match args.secrets_commands:
            case "export":
                from ...secrets import handleExportSec

                provider_name = args.export_commands
                provider_class = None
                if provider_eps:
                    for ep in provider_eps:
                        p_class = ep.load()
                        _, p_cli_name = p_class.get_cli_name()
                        if p_cli_name == provider_name:
                            provider_class = p_class
                            break

                if not provider_class:
                    raise ValueError(f"Provider '{provider_name}' not found.")

                export_arg_names = provider_class.get_export_arg_names()
                kwargs = {
                    name: getattr(args, name)
                    for name in export_arg_names
                    if hasattr(args, name)
                }

                provider_specific_args = provider_class.build_export_args(**kwargs)

                payload = SecretsExportPayload(
                    provider_name=args.export_commands,
                    key_type=args.key_type,
                    no_import=getattr(args, "no_import", False),
                    save_to_config=getattr(args, "save_to_config", False),
                    item_name=getattr(args, "item_name", None),
                    keys=getattr(args, "keys", None),
                    vault_addr=getattr(args, "vault_addr", None),
                    fingerprints=getattr(args, "fingerprints", None),
                    provider_specific_args=provider_specific_args,
                )

                handleExportSec(payload, global_config)

            case "import":
                from ...secrets import handleImportSec

                provider_name = args.import_commands
                provider_class = None
                if provider_eps:
                    for ep in provider_eps:
                        p_class = ep.load()
                        _, p_cli_name = p_class.get_cli_name()
                        if p_cli_name == provider_name:
                            provider_class = p_class
                            break

                if not provider_class:
                    raise ValueError(f"Provider '{provider_name}' not found.")

                import_arg_names = provider_class.get_import_arg_names()
                kwargs = {
                    name: getattr(args, name)
                    for name in import_arg_names
                    if hasattr(args, name)
                }

                provider_specific_args = provider_class.build_import_args(**kwargs)

                payload = SecretsImportPayload(
                    provider_name=args.import_commands,
                    key_type=args.key_type,
                    item_id=getattr(args, "item_id", None),
                    provider_specific_args=provider_specific_args,
                )

                handleImportSec(payload, global_config)

            case "rotate-add":
                from ...secrets import gatherRotateAdd, handleRotateAdd

                payload = SecretsRotatePayload(
                    type=args.type,
                    keys=args.keys,
                    context=context,
                    index=getattr(args, "index", None),
                    pgp_server=getattr(args, "pgp_server", None),
                    create=getattr(args, "create", False),
                )

                request = gatherRotateAdd(payload)
                if request:
                    from rich.prompt import Confirm

                    for field in request.fields:
                        if field.name == "update_confirmed":
                            if Confirm.ask(str(field.prompt), default=field.default):
                                payload.update_confirmed = True

                result = handleRotateAdd(payload)

                if not result.success and result.error:
                    for err in result.error:
                        console.print(f"[bold red]ERROR:[/] {err}")
                    for msg in result.message:
                        console.print(msg)
                    sys.exit(1)

                if result.error:
                    for err in result.error:
                        console.print(f"[bold red]ERROR:[/] {err}")

                if result.message:
                    for msg in result.message:
                        console.print(msg)

            case "rotate-rm":
                from ...secrets import gatherRotateRemove, handleRotateRemove

                payload = SecretsRotatePayload(
                    type=args.type,
                    keys=args.keys,
                    context=context,
                    index=getattr(args, "index", None),
                )

                request = gatherRotateRemove(payload)
                if request:
                    from rich.prompt import Confirm

                    for field in request.fields:
                        if field.name == "update_confirmed":
                            if Confirm.ask(str(field.prompt), default=field.default):
                                payload.update_confirmed = True

                result = handleRotateRemove(payload)
                if result.message:
                    for msg in result.message:
                        console.print(msg)
                if result.error:
                    for err in result.error:
                        console.print(f"[bold red]ERROR:[/] {err}")
                if not result.success:
                    sys.exit(1)

            case "list":
                from ...secrets import listFp

                payload = SecretsListPayload(
                    type=args.type,
                    context=context,
                    no_pretty=getattr(args, "no_pretty", False),
                    json=getattr(args, "json", False),
                    value=getattr(args, "value", False),
                )

                result: ResultPayload = listFp(payload)
                results = result.data

                if result.error:
                    for error in result.message:
                        console.print(f"[bold red][italic]ERROR:[/] {error}")
                        return

                if results:
                    if payload.no_pretty:
                        if payload.value:
                            print("\n".join(results))

                        elif payload.json:
                            import json

                            print(json.dumps(list(results), indent=2))

                        else:
                            from omegaconf import OmegaConf

                            print(OmegaConf.to_yaml(list(results)))

                    from chaos.lib.display_utils import render_list_as_table

                    title = f"[italic][green]Found {payload.type} Keys:[/][/]"
                    render_list_as_table(list(results), title)
                else:
                    from rich.console import Console

                    console = Console()
                    console.print(f"[cyan]INFO:[/] No {payload.type} keys to be shown.")
            case "edit":
                from ...secrets import handleSecEdit

                payload = SecretsEditPayload(
                    context=context, edit_sops_file=getattr(args, "sops", False)
                )

                result = handleSecEdit(payload)

                if result.error:
                    for err in result.error:
                        console.print(f"[bold red]ERROR:[/] {err}")

                    if result.message:
                        for msg in result.message:
                            console.print(msg)

                import os
                import subprocess

                try:
                    if payload.edit_sops_file:
                        editor = os.getenv("EDITOR", "nano")
                        subprocess.run([editor, result.data["sops_file"]], check=True)

                    elif result.data["provider"]:
                        result.data["provider"].edit(
                            result.data["secrets_file"], result.data["sops_file"]
                        )

                    else:
                        subprocess.run(
                            [
                                "sops",
                                "--config",
                                result.data["sops_file"],
                                result.data["secrets_file"],
                            ],
                            check=True,
                        )

                except subprocess.CalledProcessError as e:
                    from rich.console import Console

                    console = Console()
                    if e.returncode == 200:  # sops exit code for no changes
                        return
                    else:
                        raise RuntimeError(
                            f"SOPS editing failed with exit code {e.returncode}."
                        ) from e
                except FileNotFoundError as e:
                    raise FileNotFoundError(
                        "'sops' command not found. Please ensure sops is installed and in your PATH."
                    ) from e

            case "set-shamir":
                from ...secrets import gatherSetShamir, handleSetShamir

                payload = SecretsSetShamirPayload(
                    index=args.index, share=args.share, context=context
                )

                request = gatherSetShamir(payload)
                if request:
                    from rich.prompt import Confirm

                    for field in request.fields:
                        if field.name == "confirmed":
                            if Confirm.ask(str(field.prompt), default=field.default):
                                payload.confirmed = True
                            else:
                                console.print("[green]Alright![/] Aborting.")
                                sys.exit(0)
                        elif field.name == "update_confirmed":
                            if Confirm.ask(str(field.prompt), default=field.default):
                                payload.update_confirmed = True

                result = handleSetShamir(payload)
                if result.message:
                    for msg in result.message:
                        console.print(msg)
                if result.error:
                    for err in result.error:
                        console.print(f"[bold red]ERROR:[/] {err}")
                if not result.success:
                    sys.exit(1)

            case "print":
                from ...secrets import handleSecPrint

                payload = SecretsPrintPayload(
                    context=context,
                    print_sops_file=getattr(args, "sops", False),
                    as_json=getattr(args, "json", False),
                )

                handleSecPrint(payload)

            case "cat":
                from ...secrets import handleSecCat

                payload = SecretsCatPayload(
                    keys=args.keys,
                    context=context,
                    cat_sops_file=getattr(args, "sops", False),
                    as_json=getattr(args, "json", False),
                    value_only=getattr(args, "value", False),
                )

                handleSecCat(payload)

            case _:
                console.print("Unsupported secrets subcommand.")
    except (
        ValueError,
        FileNotFoundError,
        PermissionError,
        RuntimeError,
        EnvironmentError,
    ) as e:
        console.print(f"[bold red]ERROR:[/] {e}")
        sys.exit(1)
