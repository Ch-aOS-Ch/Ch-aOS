def handleStyx(args):
    from chaos.lib.args.dataclasses import StyxPayload
    from chaos.lib.styx import handle_styx

    payload = StyxPayload(
        styx_commands=args.styx_commands,
        entries=getattr(args, "entries", []),
        no_pretty=getattr(args, "no_pretty", False),
        json=getattr(args, "json", False),
    )
    handle_styx(payload)
