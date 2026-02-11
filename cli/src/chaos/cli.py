#!/usr/bin/env python3
import os
import sys
from typing import cast

from chaos.lib.args.args import (
    argParsing,
    handleGenerateTab,
)
from chaos.lib.args.types import ChaosArguments

"""
Ok so, this is the main CLI entrypoint for this project. Yeah, ik it's a lot of match cases, but this is intentional.
This allows us to have a very clear, explicit mapping of commands, subcommands, and their prerequisites.

To add a new command, simply add a new case to the main match statement, import the modules INSIDE the case, add a try/except and call the functions.
If a command has subcommands, add a NESTED match statement inside the case for that command, DO NOT create sepparate functions for each subcommand, let's keep them all together for clarity.

Keep this file AS EXPLICIT as possible, avoid abstractions that hide the control flux, as removing commands is way more important than adding them.
"""


def main():
    try:
        parser = argParsing()

        if "_ARGCOMPLETE" in os.environ:
            import argcomplete

            argcomplete.autocomplete(parser)

        if len(sys.argv) == 1:
            parser.print_help(sys.stderr)
            sys.exit(1)

        args = cast(ChaosArguments, parser.parse_args())

        from rich.console import Console

        match args.command:
            case "team":
                handleTeam(args, Console())

            case "styx":
                handleStyx(args, Console())

            case "explain":
                handleExplain(args)

            case "apply":
                handleApply(args, Console())

            case "secrets":
                handleSecrets(args, Console())

            case "check":
                handleCheck(args)

            case "set":
                handleSet(args, Console())

            case "ramble":
                handleRamble(args, Console())

            case "init":
                handleInit(args, Console())

            case _:
                handle_(args, Console())

    except ImportError as e:
        print(
            f"Error: Missing dependency. Please ensure all requirements are installed. Details: {e}",
            file=sys.stderr,
        )
        sys.exit(1)
    except KeyboardInterrupt:
        print("\nOperation cancelled by user.", file=sys.stderr)
        sys.exit(1)


def handleStyx(args, Console):
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
                    Console.print(listing)

            case "destroy":
                from chaos.lib.styx import uninstall_styx_entries

                entries: list[str] = args.entries
                uninstall_styx_entries(entries)
            case _:
                Console.print("Unsupported styx subcommand.")
    except (ValueError, FileNotFoundError, RuntimeError, EnvironmentError) as e:
        Console.print(f"[bold red]ERROR:[/] {e}")
        sys.exit(1)


def handleTeam(args, Console):
    try:
        match args.team_commands:
            case "list":
                from chaos.lib.args.dataclasses import TeamListPayload
                from chaos.lib.team import listTeams

                payload = TeamListPayload(
                    company=args.company, no_pretty=args.no_pretty, json=args.json
                )

                listTeams(payload)
            case "activate":
                from chaos.lib.args.dataclasses import TeamActivatePayload
                from chaos.lib.team import activateTeam

                payload = TeamActivatePayload(path=args.path)

                activateTeam(payload)
            case "init":
                from chaos.lib.args.dataclasses import TeamInitPayload
                from chaos.lib.team import initTeam

                payload = TeamInitPayload(
                    target=args.target,
                    path=args.path,
                    i_know_what_im_doing=args.i_know_what_im_doing,
                )

                initTeam(payload)
            case "clone":
                from chaos.lib.args.dataclasses import TeamClonePayload
                from chaos.lib.team import cloneGitTeam

                payload = TeamClonePayload(target=args.target, path=args.path)

                cloneGitTeam(payload)
            case "deactivate":
                from chaos.lib.args.dataclasses import TeamDeactivatePayload
                from chaos.lib.team import deactivateTeam

                payload = TeamDeactivatePayload(company=args.company, teams=args.teams)

                deactivateTeam(payload)
            case "prune":
                from chaos.lib.args.dataclasses import TeamPrunePayload
                from chaos.lib.team import pruneTeams

                payload = TeamPrunePayload(
                    companies=args.companies,
                    i_know_what_im_doing=args.i_know_what_im_doing,
                )

                pruneTeams(payload)
            case _:
                Console.print("Unsupported team subcommand.")
    except (
        ValueError,
        FileNotFoundError,
        FileExistsError,
        RuntimeError,
        EnvironmentError,
    ) as e:
        Console.print(f"[bold red]ERROR:[/] {e}")
        sys.exit(1)


def handleExplain(args):
    from chaos.lib.explain import handleExplain

    if args.topics:
        from chaos.lib.args.dataclasses import ExplainPayload
        from chaos.lib.plugDiscovery import get_plugins

        payload = ExplainPayload(
            topics=args.topics,
            complexity=args.complexity,
            details=args.details,
            no_pretty=args.no_pretty,
            json=args.json,
        )

        EXPLANATIONS = get_plugins(args.update_plugins)[2]
        handleExplain(payload, EXPLANATIONS)
    else:
        print("No explanation passed.")


# TODO: add payload
def handleApply(args, Console):
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
        Console.print(f"[bold red]ERROR:[/] {e}")
        sys.exit(1)

    except pyinfra_exceptions.PyinfraError as e:
        print(f"Unexpected pyinfra error: {e}", file=sys.stderr)
        sys.exit(1)

    except (RuntimeError, ValueError) as e:
        Console.print(f"[bold red]ERROR:[/] {e}")
        sys.exit(1)


def handleSecrets(args, Console):
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
        sops_file_override = getattr(args, "sops_file", None)
        secrets_file_override = getattr(args, "secrets_file", None)

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
                from .lib.secrets import handleExportSec

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
                from .lib.secrets import handleImportSec

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
                from .lib.secrets import handleRotateAdd

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
                from .lib.secrets import handleRotateRemove

                payload = SecretsRotatePayload(
                    type=args.type,
                    keys=args.keys,
                    context=context,
                    index=getattr(args, "index", None),
                )

                handleRotateRemove(payload)

            case "list":
                from .lib.secrets import listFp

                payload = SecretsListPayload(
                    type=args.type,
                    context=context,
                    no_pretty=getattr(args, "no_pretty", False),
                    json=getattr(args, "json", False),
                    value=getattr(args, "value", False),
                )

                listFp(payload)

            case "edit":
                from .lib.secrets import handleSecEdit

                payload = SecretsEditPayload(
                    context=context, edit_sops_file=getattr(args, "sops", False)
                )

                handleSecEdit(payload)

            case "set-shamir":
                from .lib.secrets import handleSetShamir

                payload = SecretsSetShamirPayload(
                    index=args.index, share=args.share, context=context
                )

                handleSetShamir(payload)

            case "print":
                from .lib.secrets import handleSecPrint

                payload = SecretsPrintPayload(
                    context=context,
                    print_sops_file=getattr(args, "sops", False),
                    as_json=getattr(args, "json", False),
                )

                handleSecPrint(payload)

            case "cat":
                from .lib.secrets import handleSecCat

                payload = SecretsCatPayload(
                    keys=args.keys,
                    context=context,
                    cat_sops_file=getattr(args, "sops", False),
                    as_json=getattr(args, "json", False),
                    value_only=getattr(args, "value", False),
                )

                handleSecCat(payload)

            case _:
                Console.print("Unsupported secrets subcommand.")
    except (
        ValueError,
        FileNotFoundError,
        PermissionError,
        RuntimeError,
        EnvironmentError,
    ) as e:
        Console.print(f"[bold red]ERROR:[/] {e}")
        sys.exit(1)


def handleCheck(args):
    from chaos.lib.checkers import (
        checkAliases,
        checkBoats,
        checkExplanations,
        checkLimanis,
        checkProviders,
        checkRoles,
    )

    match args.checks:
        case "explanations":
            from chaos.lib.plugDiscovery import get_plugins

            EXPLANATIONS = get_plugins(args.update_plugins)[2]
            checkExplanations(EXPLANATIONS, args.json)
        case "aliases":
            from chaos.lib.plugDiscovery import get_plugins

            ROLE_ALIASES = get_plugins(args.update_plugins)[1]
            checkAliases(ROLE_ALIASES, args.json)
        case "roles":
            from chaos.lib.plugDiscovery import get_plugins

            role_specs = get_plugins(args.update_plugins)[0]
            checkRoles(role_specs, args.json)
        case "providers":
            from chaos.lib.plugDiscovery import get_plugins

            providers = get_plugins(args.update_plugins)[4]
            checkProviders(providers, args.json)

        case "boats":
            from chaos.lib.plugDiscovery import get_plugins

            boats = get_plugins(args.update_plugins)[5]
            checkBoats(boats)

        case "secrets":
            from chaos.lib.checkers import checkSecrets
            from chaos.lib.secret_backends.utils import get_sops_files

            sec_file = get_sops_files(
                getattr(args, "sops_file", None),
                getattr(args, "secrets_file", None),
                getattr(args, "team", None),
            )[0]
            checkSecrets(sec_file, args.json)

        case "limanis":
            from chaos.lib.plugDiscovery import get_plugins

            limanis = get_plugins(args.update_plugins)[6]
            checkLimanis(limanis, args.json)

        case _:
            print(
                "No valid checks passed, valid checks: explain, alias, roles, secrets"
            )

    sys.exit(0)


def handleSet(args, Console):
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
            Console.print(f"[bold red]ERROR:[/] {e}")
            sys.exit(1)
        sys.exit(0)


def handleRamble(args, Console):
    try:
        from .lib.args.dataclasses import (
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
        from .lib.utils import get_providerEps

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
                from .lib.ramble import handleCreateRamble

                payload = RambleCreatePayload(
                    target=args.target,
                    encrypt=getattr(args, "encrypt", False),
                    keys=getattr(args, "keys", None),
                    context=ramble_context,
                )

                handleCreateRamble(payload)
            case "edit":
                from .lib.ramble import handleEditRamble

                payload = RambleEditPayload(
                    target=args.target,
                    edit_sops_file=getattr(args, "sops", False),
                    context=ramble_context,
                )

                handleEditRamble(payload)
            case "encrypt":
                from .lib.ramble import handleEncryptRamble

                payload = RambleEncryptPayload(
                    target=args.target,
                    keys=getattr(args, "keys", None),
                    context=ramble_context,
                )

                handleEncryptRamble(payload)
            case "read":
                from .lib.ramble import handleReadRamble

                payload = RambleReadPayload(
                    targets=args.targets,
                    no_pretty=getattr(args, "no_pretty", False),
                    json=getattr(args, "json", False),
                    values=getattr(args, "values", None),
                    context=ramble_context,
                )

                handleReadRamble(payload)
            case "find":
                from .lib.ramble import handleFindRamble

                payload = RambleFindPayload(
                    find_term=getattr(args, "find_term", None),
                    tag=getattr(args, "tag", None),
                    no_pretty=getattr(args, "no_pretty", False),
                    json=getattr(args, "json", False),
                    context=ramble_context,
                )

                handleFindRamble(payload)
            case "move":
                from .lib.ramble import handleMoveRamble

                payload = RambleMovePayload(
                    old=args.old,
                    new=args.new,
                    context=ramble_context,
                )

                handleMoveRamble(payload)
            case "delete":
                from .lib.ramble import handleDelRamble

                payload = RambleDeletePayload(
                    ramble=args.ramble,
                    context=ramble_context,
                )

                handleDelRamble(payload)
            case "update":
                from .lib.ramble import handleUpdateEncryptRamble

                payload = RambleUpdateEncryptPayload(
                    context=ramble_context,
                )

                handleUpdateEncryptRamble(payload)
            case _:
                Console.print("Unsupported ramble subcommand.")
    except (
        ValueError,
        FileNotFoundError,
        PermissionError,
        RuntimeError,
        FileExistsError,
    ) as e:
        Console.print(f"[bold red]ERROR:[/] {e}")
        sys.exit(1)


def handleInit(args, Console):
    try:
        from chaos.lib.inits import initChobolo, initSecrets

        match args.init_command:
            case "chobolo":
                from omegaconf import OmegaConf as oc

                from chaos.lib.plugDiscovery import get_plugins

                keys = get_plugins(args.update_plugins)[3]
                conf = initChobolo(keys)

                if not args.template:
                    path = os.path.expanduser("~/.config/chaos/ch-obolo_template.yml")
                    oc.save(conf, path)

                else:
                    if args.human:
                        print(oc.to_yaml(conf, resolve=True))
                    else:
                        print(conf)

            case "secrets":
                initSecrets()
            case _:
                Console.print("Unsupported init.")
    except (EnvironmentError, FileNotFoundError, ValueError, RuntimeError) as e:
        Console.print(f"[bold red]ERROR:[/] {e}")
        sys.exit(1)


def handle_(args, Console):
    if args.generate_tab:
        handleGenerateTab()
        sys.exit(0)

    elif args.edit_chobolo:
        try:
            from chaos.lib.tinyScript import runChoboloEdit

            runChoboloEdit(args.chobolo)
        except (ValueError, FileNotFoundError, RuntimeError) as e:
            Console.print(f"[bold red]ERROR:[/] {e}")
            sys.exit(1)

    elif args.update_plugins:
        try:
            from chaos.lib.plugDiscovery import get_plugins

            get_plugins(update_cache=True)
            Console.print("[bold green]Plugins updated successfully.[/]")
            sys.exit(0)
        except (RuntimeError, EnvironmentError) as e:
            Console.print(f"[bold red]ERROR:[/] {e}")
            sys.exit(1)


if __name__ == "__main__":
    main()
