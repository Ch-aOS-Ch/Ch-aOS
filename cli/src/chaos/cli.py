#!/usr/bin/env python3
import sys
import argcomplete

from chaos.lib.plugDiscovery import get_plugins
from chaos.lib.args import handleGenerateTab, argParsing

def main():
    from pyinfra.api import exceptions as pyinfra_exceptions

    try:
        parser = argParsing()

        argcomplete.autocomplete(parser)

        args = parser.parse_args()

        role_specs, ROLE_ALIASES, EXPLANATIONS, keys = get_plugins(args.update_plugins)

        if hasattr(args, 'command') and args.command == 'explain':
            from chaos.lib.handlers import handleExplain
            if args.topics:
                handleExplain(args, EXPLANATIONS)
            else:
                print("No explanation passed.")

        elif hasattr(args, 'command') and args.command == 'apply':
            from chaos.lib.plugDiscovery import load_roles
            from chaos.lib.handlers import handleVerbose, handleOrchestration

            ROLES_DISPATCHER = load_roles(role_specs)
            ikwid = args.i_know_what_im_doing
            dry = args.dry
            if args.verbose or args.v > 0:
                handleVerbose(args)
            if args.tags:
                handleOrchestration(args, dry, ikwid, ROLES_DISPATCHER, ROLE_ALIASES)
            else:
                print("No tags passed.")

        elif hasattr(args, 'command') and args.command == 'check':
            from chaos.lib.checkers import checkAliases, checkExplanations, checkRoles
            from chaos.lib.tinyScript import runSopsCheck

            user_checks = set(args.checks)
            alias_checks = {'alias', 'aliases', 'a'}
            role_checks = {'role', 'roles', 'r'}
            explain_checks = {'explain', 'explanations', 'e'}
            sec_checks = {'secrets', 'secs', 'sec', 's'}

            if alias_checks.intersection(user_checks):
                checkAliases(ROLE_ALIASES)
            if role_checks.intersection(user_checks):
                checkRoles(role_specs)
            if explain_checks.intersection(user_checks):
                checkExplanations(EXPLANATIONS)
            if sec_checks.intersection(user_checks):
                runSopsCheck(args.sops_file_override, args.secrets_file_override)

            if not any(c.intersection(user_checks) for c in [alias_checks, role_checks, explain_checks, sec_checks]):
                print("No valid checks passed, valid checks: explain, alias, roles, secrets")
            sys.exit(0)

        elif hasattr(args, 'command') and args.command == 'set':
            from chaos.lib.handlers import setMode
            is_setter_mode = any([
                hasattr(args, 'chobolo_file') and args.chobolo_file,
                hasattr(args, 'secrets_file') and args.secrets_file,
                hasattr(args, 'sops_file') and args.sops_file
            ])
            if is_setter_mode:
                setMode(args)
                sys.exit(0)

        elif hasattr(args, 'command') and args.command == 'ramble':
            from chaos.lib.handlers import (
                handleCreateRamble, handleEditRamble, handleEncryptRamble,
                handleReadRamble, handleFindRamble, handleMoveRamble, handleDelRamble
            )
            match args.ramble_commands:
                case 'create': handleCreateRamble(args)
                case 'edit': handleEditRamble(args)
                case 'encrypt': handleEncryptRamble(args)
                case 'read': handleReadRamble(args)
                case 'find': handleFindRamble(args)
                case 'move': handleMoveRamble(args)
                case 'delete': handleDelRamble(args)

        elif hasattr(args, 'command') and args.command == 'init':
            from chaos.lib.inits import initChobolo, initSecrets
            if args.init_command == 'chobolo':
                initChobolo(keys)
            elif args.init_command == 'secrets':
                initSecrets()

        elif args.generate_tab:
            handleGenerateTab()
            sys.exit(0)

        elif args.edit_sec:
            from chaos.lib.tinyScript import runSopsEdit
            runSopsEdit(args.sops_file_override, args.secrets_file_override)
            sys.exit(0)

        elif args.edit_chobolo:
            from chaos.lib.tinyScript import runChoboloEdit
            runChoboloEdit(args.chobolo)
            sys.exit(0)

    except ImportError as e:
        print(f"Error: Missing dependency. Please ensure all requirements are installed. Details: {e}", file=sys.stderr)
        sys.exit(1)
    except pyinfra_exceptions.PyinfraError as e:
        print(f"Unexpected pyinfra error: {e}", file=sys.stderr)
        sys.exit(1)
    except KeyboardInterrupt:
        print("\nOperation cancelled by user.", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
  main()
