#!/usr/bin/env python3
import sys
import argcomplete
from chaos.lib.args import handleGenerateTab, argParsing

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

        argcomplete.autocomplete(parser)

        args = parser.parse_args()

        from rich.console import Console


        match args.command:
            case 'team':
                try:
                    match args.team_commands:
                        case 'list':
                            from chaos.lib.team import listTeams
                            listTeams(args)
                        case 'activate':
                            from chaos.lib.team import activateTeam
                            activateTeam(args)
                        case 'init':
                            from chaos.lib.team import initTeam
                            initTeam(args)
                        case 'clone':
                            from chaos.lib.team import cloneGitTeam
                            cloneGitTeam(args)
                        case 'deactivate':
                            from chaos.lib.team import deactivateTeam
                            deactivateTeam(args)
                        case 'prune':
                            from chaos.lib.team import pruneTeams
                            pruneTeams(args)
                        case _:
                            Console().print("Unsupported team subcommand.")
                except (ValueError, FileNotFoundError, FileExistsError, RuntimeError, EnvironmentError) as e:
                    Console().print(f"[bold red]ERROR:[/] {e}")
                    sys.exit(1)

            case 'explain':
                from chaos.lib.handlers import handleExplain
                if args.topics:
                    from chaos.lib.plugDiscovery import get_plugins
                    _, _, EXPLANATIONS, _ = get_plugins(args.update_plugins)
                    handleExplain(args, EXPLANATIONS)
                else:
                    print("No explanation passed.")

            case 'apply':
                from chaos.lib.plugDiscovery import load_roles
                from chaos.lib.handlers import handleVerbose, handleOrchestration
                from pyinfra.api import exceptions as pyinfra_exceptions # type: ignore
                from typing import cast
                from omegaconf import DictConfig

                """
                The apply command needs some special handling, as it is the main entry point for OS orchestration.
                We load the roles, handle verbosity, and then pass control to the orchestration handler.
                """
                try:
                    from chaos.lib.plugDiscovery import get_plugins
                    role_specs, ROLE_ALIASES, _, _ = get_plugins(args.update_plugins)
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
                    Console().print(f"[bold red]ERROR:[/] {e}")
                    sys.exit(1)
                except pyinfra_exceptions.PyinfraError as e:
                    print(f"Unexpected pyinfra error: {e}", file=sys.stderr)
                    sys.exit(1)

            case 'secrets':
                try:
                    from chaos.lib.secrets import(
                        handleRotateAdd,
                        handleRotateRemove,
                        listFp,
                        handleSetShamir,
                        handleSecEdit,
                        handleSecPrint,
                        handleSecCat
                    )
                    from chaos.lib.secret_backends.utils import get_sops_files
                    team = getattr(args, 'team', None)
                    sops_file_override = getattr(args, 'sops_file', None)
                    secrets_file_override = getattr(args, 'secrets_file', None)
                    _, _, global_config = get_sops_files(sops_file_override, secrets_file_override, team)
                    match args.secrets_commands:
                        case 'export':
                            match args.export_commands:
                                case 'bw':
                                    from chaos.lib.secret_backends.bitwarden import BitwardenPasswordProvider
                                    provider = BitwardenPasswordProvider(args, global_config)
                                    provider.export_secrets()
                                case 'bws':
                                    from chaos.lib.secret_backends.bitwarden import BitwardenSecretsProvider
                                    provider = BitwardenSecretsProvider(args, global_config)
                                    provider.export_secrets()
                                case 'op':
                                    from chaos.lib.secret_backends.onepassword import OnePasswordProvider
                                    provider = OnePasswordProvider(args, global_config)
                                    provider.export_secrets()
                        case 'import':
                            match args.import_commands:
                                case 'bw':
                                    from chaos.lib.secret_backends.bitwarden import BitwardenPasswordProvider
                                    provider = BitwardenPasswordProvider(args, global_config)
                                    provider.import_secrets()
                                case 'bws':
                                    from chaos.lib.secret_backends.bitwarden import BitwardenSecretsProvider
                                    provider = BitwardenSecretsProvider(args, global_config)
                                    provider.import_secrets()
                                case 'op':
                                    from chaos.lib.secret_backends.onepassword import OnePasswordProvider
                                    provider = OnePasswordProvider(args, global_config)
                                    provider.import_secrets()
                        case 'rotate-add': handleRotateAdd(args)
                        case 'rotate-rm': handleRotateRemove(args)
                        case 'list': listFp(args)
                        case 'edit': handleSecEdit(args)
                        case 'shamir': handleSetShamir(args)
                        case 'print': handleSecPrint(args)
                        case 'cat': handleSecCat(args)
                        case _:
                            Console().print("Unsupported secrets subcommand.")
                except (ValueError, FileNotFoundError, PermissionError, RuntimeError, EnvironmentError) as e:
                    Console().print(f"[bold red]ERROR:[/] {e}")
                    sys.exit(1)

            case 'check':
                from chaos.lib.checkers import checkAliases, checkExplanations, checkRoles

                match args.checks:
                    case 'explanations':
                        from chaos.lib.plugDiscovery import get_plugins
                        _, _, EXPLANATIONS, _ = get_plugins(args.update_plugins)
                        checkExplanations(EXPLANATIONS)
                    case 'aliases':
                        from chaos.lib.plugDiscovery import get_plugins
                        _, ROLE_ALIASES, _, _ = get_plugins(args.update_plugins)
                        checkAliases(ROLE_ALIASES)
                    case 'roles':
                        from chaos.lib.plugDiscovery import get_plugins
                        role_specs, _, _, _ = get_plugins(args.update_plugins)
                        checkRoles(role_specs)
                    case _: print("No valid checks passed, valid checks: explain, alias, roles, secrets")

                sys.exit(0)

            case 'set':
                from chaos.lib.handlers import setMode
                is_setter_mode = any([
                    hasattr(args, 'chobolo_file') and args.chobolo_file,
                    hasattr(args, 'secrets_file') and args.secrets_file,
                    hasattr(args, 'sops_file') and args.sops_file
                ])
                if is_setter_mode:
                    try:
                        setMode(args)
                    except FileNotFoundError as e:
                        Console().print(f"[bold red]ERROR:[/] {e}")
                        sys.exit(1)
                    sys.exit(0)

            case 'ramble':
                try:
                    from chaos.lib.ramble import (
                        handleCreateRamble, handleEditRamble, handleEncryptRamble,
                        handleReadRamble, handleFindRamble, handleMoveRamble, handleDelRamble,
                        handleUpdateEncryptRamble
                    )
                    match args.ramble_commands:
                        case 'create': handleCreateRamble(args)
                        case 'edit': handleEditRamble(args)
                        case 'encrypt': handleEncryptRamble(args)
                        case 'read': handleReadRamble(args)
                        case 'find': handleFindRamble(args)
                        case 'move': handleMoveRamble(args)
                        case 'delete': handleDelRamble(args)
                        case 'update': handleUpdateEncryptRamble(args)
                        case _:
                            Console().print("Unsupported ramble subcommand.")
                except (ValueError, FileNotFoundError, PermissionError, RuntimeError, FileExistsError) as e:
                    Console().print(f"[bold red]ERROR:[/] {e}")
                    sys.exit(1)

            case 'init':
                try:
                    from chaos.lib.inits import initChobolo, initSecrets
                    match args.init_command:
                        case 'chobolo':
                            from chaos.lib.plugDiscovery import get_plugins
                            _, _, _, keys = get_plugins(args.update_plugins)
                            initChobolo(keys)
                        case 'secrets': initSecrets()
                        case _:
                            Console().print("Unsupported init.")
                except (EnvironmentError, FileNotFoundError, ValueError, RuntimeError) as e:
                    Console().print(f"[bold red]ERROR:[/] {e}")
                    sys.exit(1)
            case _:
                if args.generate_tab:
                    handleGenerateTab()
                    sys.exit(0)

                elif args.edit_chobolo:
                    try:
                        from chaos.lib.tinyScript import runChoboloEdit
                        runChoboloEdit(args.chobolo)
                    except (ValueError, FileNotFoundError, RuntimeError) as e:
                        Console().print(f"[bold red]ERROR:[/] {e}")
                        sys.exit(1)

        sys.exit(0)

    except ImportError as e:
        print(f"Error: Missing dependency. Please ensure all requirements are installed. Details: {e}", file=sys.stderr)
        sys.exit(1)
    except KeyboardInterrupt:
        print("\nOperation cancelled by user.", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
  main()
