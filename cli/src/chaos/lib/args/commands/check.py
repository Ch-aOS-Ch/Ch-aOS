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
    handle_check(payload)
