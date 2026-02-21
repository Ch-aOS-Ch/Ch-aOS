"""
Welcome to the Ch-aOS project suite!

Please note that we use a mix of LoB with a tiny little bit of OOP (and clean code for that matter) in this project.
We prefer to keep things simple and straightforward, instead of over-abstracting things, focus on readability and
Locality of Behavior. This makes the life of everyone easier, since you don't need to keep on jumping from function to function
class to class and file to file to understand the flow of the code. You can just read it from top to bottom and understand it in one go.

Best practices are important, but they should not come at the cost of readability and simplicity. We want to keep the codebase as simple
as possible, while still being maintainable and extensible.

Best practices for this project:
    If you repeat yourself >= 3 times, refactor it into a function or a class (more about classes later).


    If you have a function that is too long, but it only does one CONCEPT (aka
        "handle the pyinfra orchestration"), then it's fine. If it does more than 2 concepts,
        refactor it and give the functions clear names and docstrings.

        Good rule of thumb is that if the function is about 100 lines long, try to reason with yourself
            about what the function is doing, if it is doing more than 2 concepts, it's time for the big ol refac hammer.

        Do note that a code review will be conducted and we will be looking at the code and giving feedback on it, so
            even if you think your code is fine, we might ask you to refactor it or to docstring it, it is not a judgmeent of
            your coding skills, we just want to keep our codebase easy to read and maintain.


    Focus on using types, yes, I know we are using python, but please do make everyone's life easier,
        we're on the modern era of LSPs and type checking, so let's use it to our advantage.


    Avoid over-abstracting things. If you create a new type of PLUGIN then make it into a class,
        but please, don't create a new class for every minute detail.


    Keep the code as simple and straightforward as possible. If you can do something in a simple way, do it.


    Avoid creating decorators. Again with the abstraction. If you NEED a decorator, 9 times out of 10 you just don't. Decorators can
        be very powerful, but they can take control away from the developer, so we want to avoid them.

        But I mean, if you really want to create a decorator, just go for it, but keep in mind that, IF it is not well documented and has
            clear intent, it might not pass the PR review. Just a heads up, we are not against them, but powerful tools need powerful
            control over commands.


    Classes are meant for representing clear contracts so we can easily plug things in and out, not for the
        sake of creating classes. If you have a clear, repeating contract, then by all means, create a class for it, but
        if you just want to create a class cause "oh, we might need to have multiple implementations of this in the future!"
        Then don't. A good example for a good class would be the Limani plugin class, we do only have a singular implementation
        for it, yes, but it allows for scalability of multiple databases for _other people_ to use. Our use-case Limani is fine
        as it is, but for other people, it might not be, so we created a clear contract and made it pluggable.


    IF you need to create a class BECAUSE of the implementation of another library (eg: pyinfra's Facts), then it is quite alright.


    Code should be CLEAR, not CLEAN. This means that you should not focus on Uncle Bob's clean code principles to a T,
        but rather focus on making the code ACTUALLY readable and understandable. If that means breaking some of the "clean code" rules,
        so be it, as long as the code is clear on intent and functionality.

        Btw, this is not an excuse to write messy, sloppy code, but rather a reminder that the ultimate goal is to have a code that is
            both easy to read, and easy to refactor if necessary.


    Imports go INSIDE of functions. We have quite a big codebase, avoiding unnecessary imports at the top level is a good practice to avoid
        circular imports and to improve the overall performance of the code as a whole. Only import what you need, when you need it.
        This also makes the code clearer on what dependencies it needs for each function, making it easier
        to optimize in the future if needed.

        The only exceptions should be standard library imports (eg: os, sys, json, etc) and DATA CONTRACTS (eg: types, interfaces, etc),
            since these are usually pretty light and help with LSPs and type checking, so we want them to be available globally.

        Now, I understand that this system of lazy imports is relatively new to python as a whole and might be a bit controversial, but
            with this architecture, we have found that we could be faster than some traditionally eager-loading tools (tests are still
            being documented but I'm writing an academic paper on this, so ye), I do understand this goes against the traditional way
            of coding in python, but we're not trying to be traditional, we're trying to be efficient and useful, and this, we found, is
            one of the best ways to do it.

        Let it be known that this is not a "You must only code python like this", but rather a architecture choice for this specific project,
            and that we will not change it any time soon, as this gives us some pretty nice benefits (I mean, the CLI started in 0.5 seconds before,
            now it starts in about 0.1s to 0.069s depending on the state of the machine, so it is a pretty nice improvement)

        Once PEP 810 hits the scene, we will check if its a good fit for our codebase (we need it to work with py3.11 in some way, since its our
            minimum supported version, if it does, we will go back to PEP8 standards for imports, just with "lazy" in front of them.
            IF it doesn't, we will keep doing what we're doing. LSPs and type checking + performance are more important than
            "code conventions" for us, so we will choose the best option for our codebase, not the one that is more "standard".


    If you display something to the user, first make it beautiful and nice for humans, then make it be beautiful and nice for machines.
        This means that if you're printing something to the user, keep in mind that the user might not want to see only a pretty table,
        but also might want to parse the output with jq or something.

        Ofc, this should only be true for specific things, if you print "Operation completed successfully!" then you don't need to make it
            machine parsable, but if you're printing a list of teams, then you should make it both human and machine friendly.


    CODE FIRST, THEN OPTIMIZE. Don't try to optimize things that don't even turn on yet.


    Docstrings, Docstrings, Docstrings. Again, LSPs, we are in the modern era people!


    Use f-strings, always. No more of that old .format() or string concatenation..


    Use auto-linters and formatters on your code, we don't care which one, but do use one.
        I personally recommend Ruff or Flake8


    Other than that, just use PEP8 and common sense, and we should be good.


About AI usage:
    While we are not strictly against the use of AI tools for _coding_, there are some rules to follow.


    1: Code reviews are mandatory for everyone, and we don't want to see any code that has not been reviewed by a HUMAN, no matter how small
        the change is.


    2: We are fine with all types of CODE AUTO COMPLETION. But we want to make sure that the code is either 1: 100% human, or 2: _helped_
        by AI, but not 100% AI generated (without human review).

        If the code you wrote is 100% AI, then it most likely will not pass the code review, but if you actually wrote something and then
            some AI to help you with it, or you used AI to generate a first draft, or even if you used AI to refactor some code you wrote,
            but you actually reviewed the code and made sure its not slop, then it should be fine. The key here is that the code should be
            reviewed by a human, and that the human should make actual relevant changes to the code, making the final architectural and
            design decisions, not the AI. The AI should be a tool to help you, not to replace you.


    3: We are against AI generating entire functions, classes or modules without human review. If you want to use AI to generate code,
        make sure it is not slop before putting a PR.


    4: AGENTS are not allowed, TOOLS are fine, but AGENTS are not. Things like gemini-cli, copilot-cli, etc, are fine, but things like
        AutoGPT, AgentGPT, etc, are not.


    5: No github.com copilot usage. I understand this is weird and all, but it is to avoid the Contributors page being flooded with bots,
        We want to make sure that all contributors are actual humans and have their name on there.

        This is by all means NOT an judgement on any tool quality, but rather a way to give shoutouts to all the amazing humans that may
            contribute to this project.


Current Works:
    We are currently decoupling the codebase from the CLI interface, and moving all the logic to a more API-friendly structure,
        so that we can easily use it in different contexts, not just the CLI, and also, this will help with typing of shtuff,
        since we can have clear data contracts.


    After this, we will be working on a webhooks API interface so that we can create a web-ui akin to Ansible-tower, but for Ch-aOS
"""


def main():
    """
    This is the main CLI entry point for this tool It handles parsing and the passage of arguments
    To the subcommand handlers in chaos.lib.args.commands. Each subcommand handler is responsible for its own logic and functionality.

    To add a new command, create a new handler in chaos.lib.args.commands and add a case for it in the main function.
    Do not forget to add a equivalent dataclass in chaos.lib.args.types for the data of the subcommand commands
    and to type the args in chaos.lib.args.types.
    """
    import sys
    from typing import cast

    from chaos.lib.args.args import argParsing
    from chaos.lib.args.types import ChaosArguments

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
