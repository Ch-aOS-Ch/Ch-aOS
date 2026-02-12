#!/usr/bin/env python3
import sys
from typing import cast

from chaos.lib.args.args import argParsing
from chaos.lib.args.types import ChaosArguments

"""
This is the main CLI entry point for this tool It handles parsing and the passage of arguments
To the subcommand handlers in chaos.lib.args.commands. Each subcommand handler is responsible for its own logic and functionality.

To add a new command, create a new handler in chaos.lib.args.commands and add a case for it in the main function.
Do not forget to add a equivalent dataclass in chaos.lib.args.types for the data of the subcommand commands
and to type the args in chaos.lib.args.types.
"""


def main():
    try:
        parser = argParsing()

        if len(sys.argv) == 1:
            parser.print_help(sys.stderr)
            sys.exit(1)

        args = cast(ChaosArguments, parser.parse_args())

        match args.command:
            case "team":
                from .lib.args.commands.team import handleTeam

                handleTeam(args)

            case "styx":
                from .lib.args.commands.styx import handleStyx

                handleStyx(args)

            case "explain":
                from .lib.args.commands.explain import handleExplain

                handleExplain(args)

            case "apply":
                from .lib.args.commands.apply import handleApply

                handleApply(args)

            case "secrets":
                from .lib.args.commands.secrets import handleSecrets

                handleSecrets(args)

            case "check":
                from .lib.args.commands.check import handleCheck

                handleCheck(args)

            case "set":
                from .lib.args.commands.set import handleSet

                handleSet(args)

            case "ramble":
                from .lib.args.commands.ramble import handleRamble

                handleRamble(args)

            case "init":
                from .lib.args.commands.init import handleInit

                handleInit(args)

            case _:
                from .lib.args.commands.extras import handle_

                handle_(args)

    except ImportError as e:
        print(
            f"Error: Missing dependency. Please ensure all requirements are installed. Details: {e}",
            file=sys.stderr,
        )
        sys.exit(1)
    except KeyboardInterrupt:
        print("\nOperation cancelled by user.", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
