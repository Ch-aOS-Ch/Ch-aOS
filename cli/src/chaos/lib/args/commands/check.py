import sys


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

        case "templates":
            from chaos.lib.checkers import checkTemplates
            from chaos.lib.plugDiscovery import get_plugins

            keys = get_plugins(args.update_plugins)[3]
            checkTemplates(keys, args.json)

        case _:
            print(
                "No valid checks passed, valid checks: explain, alias, roles, secrets"
            )

    sys.exit(0)
