#!/usr/bin/env python3
import sys
from typing import cast

from chaos.lib.args.args import argParsing
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
