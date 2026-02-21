from chaos.lib.args.dataclasses import ResultPayload


def handleCheck(args):
    from chaos.lib.args.dataclasses import CheckPayload
    from chaos.lib.checkers import handle_check

    payload = CheckPayload(
        checks=args.checks,
        chobolo=getattr(args, "chobolo", None),
        json=getattr(args, "json", False),
        team=getattr(args, "team", None),
        sops_file_override=getattr(args, "sops_file_override", None),
        secrets_file_override=getattr(args, "secrets_file_override", None),
        update_plugins=getattr(args, "update_plugins", False),
    )

    result: ResultPayload = handle_check(payload)

    if result.success:
        from chaos.lib.checkers import printCheck

        printCheck(payload.checks, result.data, json_output=payload.json)
