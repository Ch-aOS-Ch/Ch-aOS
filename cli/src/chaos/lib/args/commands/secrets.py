import sys


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
                from ...secrets import handleRotateAdd

                payload = SecretsRotatePayload(
                    type=args.type,
                    keys=args.keys,
                    context=context,
                    index=getattr(args, "index", None),
                    pgp_server=getattr(args, "pgp_server", None),
                    create=getattr(args, "create", False),
                )

                handleRotateAdd(payload)

            case "rotate-rm":
                from ...secrets import handleRotateRemove

                payload = SecretsRotatePayload(
                    type=args.type,
                    keys=args.keys,
                    context=context,
                    index=getattr(args, "index", None),
                )

                handleRotateRemove(payload)

            case "list":
                from ...secrets import listFp

                payload = SecretsListPayload(
                    type=args.type,
                    context=context,
                    no_pretty=getattr(args, "no_pretty", False),
                    json=getattr(args, "json", False),
                    value=getattr(args, "value", False),
                )

                listFp(payload)

            case "edit":
                from ...secrets import handleSecEdit

                payload = SecretsEditPayload(
                    context=context, edit_sops_file=getattr(args, "sops", False)
                )

                handleSecEdit(payload)

            case "set-shamir":
                from ...secrets import handleSetShamir

                payload = SecretsSetShamirPayload(
                    index=args.index, share=args.share, context=context
                )

                handleSetShamir(payload)

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
