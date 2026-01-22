#!/usr/bin/env python3
import sys
import os
from typing import cast
from chaos.lib.args.args import (
    handleGenerateTab,
    argParsing,
    addTeamParsers,
    addExplainParsers,
    addApplyParsers,
    addSecParsers,
    addCheckParsers,
    addSetParsers,
    addRambleParsers,
    addInitParsers
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
            case 'team':
                handleTeam(args, Console())

            case 'styx':
                handleStyx(args, Console())

            case 'explain':
                handleExplain(args)

            case 'apply':
                handleApply(args, Console())

            case 'secrets':
                handleSecrets(args, Console())

            case 'check':
                handleCheck(args)

            case 'set':
                handleSet(args, Console())

            case 'ramble':
                handleRamble(args, Console())

            case 'init':
                handleInit(args, Console())

            case _:
                handle_(args, Console())

    except ImportError as e:
        print(f"Error: Missing dependency. Please ensure all requirements are installed. Details: {e}", file=sys.stderr)
        sys.exit(1)
    except KeyboardInterrupt:
        print("\nOperation cancelled by user.", file=sys.stderr)
        sys.exit(1)

def handleStyx(args, Console):
    try:
        match args.styx_commands:
            case 'invoke':
                from chaos.lib.styx import install_styx_entries
                entries = args.entries
                install_styx_entries(entries)

            case 'list':
                from chaos.lib.styx import list_styx_entries
                entries = args.entries
                listing = list_styx_entries(entries, args.no_pretty, args.json)
                if args.no_pretty:
                    print(listing)
                else:
                    Console.print(listing)

            case 'destroy':
                from chaos.lib.styx import uninstall_styx_entries
                entries = args.entries
                uninstall_styx_entries(entries)
            case _:
                Console.print("Unsupported styx subcommand.")
    except (ValueError, FileNotFoundError, RuntimeError, EnvironmentError) as e:
        Console.print(f"[bold red]ERROR:[/] {e}")
        sys.exit(1)

def handleTeam(args, Console):
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
                Console.print("Unsupported team subcommand.")
    except (ValueError, FileNotFoundError, FileExistsError, RuntimeError, EnvironmentError) as e:
        Console.print(f"[bold red]ERROR:[/] {e}")
        sys.exit(1)

def handleExplain(args):
    from chaos.lib.explain import handleExplain
    if args.topics:
        from chaos.lib.plugDiscovery import get_plugins
        EXPLANATIONS = get_plugins(args.update_plugins)[2]
        handleExplain(args, EXPLANATIONS)
    else:
        print("No explanation passed.")

def handleApply(args, Console):
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
    except RuntimeError as e:
        Console.print(f"[bold red]ERROR:[/] {e}")
        sys.exit(1)

def handleSecrets(args, Console):
    try:
        from chaos.lib.secrets import(
            handleRotateAdd,
            handleRotateRemove,
            listFp,
            handleSetShamir,
            handleSecEdit,
            handleSecPrint,
            handleSecCat,
            handleImportSec,
            handleExportSec
        )
        from chaos.lib.secret_backends.utils import get_sops_files
        team = getattr(args, 'team', None)
        sops_file_override = getattr(args, 'sops_file', None)
        secrets_file_override = getattr(args, 'secrets_file', None)
        _, _, global_config = get_sops_files(sops_file_override, secrets_file_override, team)
        match args.secrets_commands:
            case 'export': handleExportSec(args, global_config)
            case 'import': handleImportSec(args, global_config)
            case 'rotate-add': handleRotateAdd(args)
            case 'rotate-rm': handleRotateRemove(args)
            case 'list': listFp(args)
            case 'edit': handleSecEdit(args)
            case 'set-shamir': handleSetShamir(args)
            case 'print': handleSecPrint(args)
            case 'cat': handleSecCat(args)
            case _:
                Console.print("Unsupported secrets subcommand.")
    except (ValueError, FileNotFoundError, PermissionError, RuntimeError, EnvironmentError) as e:
        Console.print(f"[bold red]ERROR:[/] {e}")
        sys.exit(1)

def handleCheck(args):
    from chaos.lib.checkers import checkAliases, checkExplanations, checkRoles, checkProviders, checkBoats

    match args.checks:
        case 'explanations':
            from chaos.lib.plugDiscovery import get_plugins
            EXPLANATIONS = get_plugins(args.update_plugins)[2]
            checkExplanations(EXPLANATIONS, args.json)
        case 'aliases':
            from chaos.lib.plugDiscovery import get_plugins
            ROLE_ALIASES = get_plugins(args.update_plugins)[1]
            checkAliases(ROLE_ALIASES, args.json)
        case 'roles':
            from chaos.lib.plugDiscovery import get_plugins
            role_specs = get_plugins(args.update_plugins)[0]
            checkRoles(role_specs, args.json)
        case 'providers':
            from chaos.lib.plugDiscovery import get_plugins
            providers = get_plugins(args.update_plugins)[4]
            checkProviders(providers, args.json)

        case 'boats':
            from chaos.lib.plugDiscovery import get_plugins
            boats = get_plugins(args.update_plugins)[5]
            checkBoats(boats)

        case 'secrets':
            from chaos.lib.secret_backends.utils import get_sops_files
            from chaos.lib.checkers import checkSecrets
            sec_file = get_sops_files(
                getattr(args, 'sops_file', None),
                getattr(args, 'secrets_file', None),
                getattr(args, 'team', None)
            )[0]
            checkSecrets(sec_file, args.json)

        case _: print("No valid checks passed, valid checks: explain, alias, roles, secrets")

    sys.exit(0)

def handleSet(args, Console):
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
            Console.print(f"[bold red]ERROR:[/] {e}")
            sys.exit(1)
        sys.exit(0)

def handleRamble(args, Console):
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
                Console.print("Unsupported ramble subcommand.")
    except (ValueError, FileNotFoundError, PermissionError, RuntimeError, FileExistsError) as e:
        Console.print(f"[bold red]ERROR:[/] {e}")
        sys.exit(1)

def handleInit(args, Console):
    try:
        from chaos.lib.inits import initChobolo, initSecrets
        match args.init_command:
            case 'chobolo':
                from chaos.lib.plugDiscovery import get_plugins
                keys = get_plugins(args.update_plugins)[3]
                initChobolo(keys, args)
            case 'secrets': initSecrets()
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
