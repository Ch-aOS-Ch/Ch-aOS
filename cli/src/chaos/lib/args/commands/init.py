def handleInit(args):
    from chaos.lib.args.dataclasses import InitPayload
    from chaos.lib.inits import handle_init

    payload = InitPayload(
        init_command=args.init_command,
        update_plugins=getattr(args, "update_plugins", False),
        targets=getattr(args, "targets", []),
        template=getattr(args, "template", False),
        human=getattr(args, "human", False),
    )

    handle_init(payload)
