#!/usr/bin/env python3
import sys

import argcomplete

from chaos.lib.plugDiscovery import get_plugins, load_roles
from chaos.lib.args import handleGenerateTab, argParsing
from chaos.lib.checkers import checkAliases, checkExplanations, checkRoles
from chaos.lib.inits import initSecrets, initChobolo

from chaos.lib.handlers import (
    handleDelRamble,
    handleMoveRamble,
    setMode,
    handleVerbose,
    handleExplain,
    handleOrchestration,
    handleCreateRamble,
    handleEditRamble,
    handleEncryptRamble,
    handleReadRamble,
    handleFindRamble
)

from chaos.lib.tinyScript import runChoboloEdit, runSopsCheck, runSopsEdit

from pyinfra.api import exceptions

def main():
    try:
        parser = argParsing()

        argcomplete.autocomplete(parser)

        args = parser.parse_args()
        role_specs, ROLE_ALIASES, EXPLANATIONS, keys = get_plugins(args.update_plugins)

        if hasattr(args, 'command') and args.command == 'explain':
            if args.topics:
                handleExplain(args, EXPLANATIONS)
            else:
                print("No explanation passed.")

        if hasattr(args, 'command') and args.command == 'apply':
            ROLES_DISPATCHER = load_roles(role_specs)
            ikwid = args.i_know_what_im_doing
            dry = args.dry
            if args.verbose or args.v > 0:
                handleVerbose(args)
            if args.tags:
                handleOrchestration(args, dry, ikwid, ROLES_DISPATCHER, ROLE_ALIASES)
            else:
                print("No tags passed.")

        if hasattr(args, 'command') and args.command == 'check':
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

            if not (sec_checks.intersection(user_checks) or explain_checks.intersection(user_checks) or role_checks.intersection(user_checks) or alias_checks.intersection(user_checks)):
                print("No valid checks passed, valid checks: explain, alias, roles, secrets")
            sys.exit(0)

        if hasattr(args, 'command') and args.command == 'set':
            is_setter_mode = any([
                hasattr(args, 'chobolo_file') and args.chobolo_file,
                hasattr(args, 'secrets_file') and args.secrets_file,
                hasattr(args, 'sops_file') and args.sops_file
            ])
            if is_setter_mode:
                setMode(args)
                sys.exit(0)

        if hasattr(args, 'command') and args.command == 'ramble':
            match args.ramble_commands:
                case 'create':
                    handleCreateRamble(args)
                case 'edit':
                    handleEditRamble(args)
                case 'encrypt':
                    handleEncryptRamble(args)
                case 'read':
                    handleReadRamble(args)
                case 'find':
                    handleFindRamble(args)
                case 'move':
                    handleMoveRamble(args)
                case 'delete':
                    handleDelRamble(args)

        if hasattr(args, 'command') and args.command == 'init':
            if args.init_command == 'chobolo':
                initChobolo(keys)
            elif args.init_command == 'secrets':
                initSecrets()

        if args.generate_tab:
            handleGenerateTab()
            sys.exit(0)

        if args.edit_sec:
            runSopsEdit(args.sops_file_override, args.secrets_file_override)
            sys.exit(0)

        if args.edit_chobolo:
            runChoboloEdit(args.chobolo)
            sys.exit(0)

    except exceptions.PyinfraError as e:
        print(f"Unexpected pyinfra error: {e}")
        sys.exit(1)
    except KeyboardInterrupt:
        print("\nOperation cancelled by user.", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
  main()
