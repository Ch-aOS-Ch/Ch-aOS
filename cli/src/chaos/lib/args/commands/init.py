from chaos.lib.args.dataclasses import ResultPayload


def handleInit(args):
    from pathlib import Path

    from chaos.lib.args.dataclasses import InitPayload
    from chaos.lib.inits import handle_init

    payload = InitPayload(
        init_command=args.init_command,
        update_plugins=getattr(args, "update_plugins", False),
        targets=getattr(args, "targets", []),
        template=getattr(args, "template", False),
        human=getattr(args, "human", False),
    )

    result: ResultPayload = handle_init(payload)

    for message in result.message:
        print(message)

    if payload.init_command == "chobolo":
        import os

        from omegaconf import OmegaConf as oc

        conf = result.data

        if not payload.template:
            path = os.getenv(
                "CHAOS_CONFIG_DIR",
                Path.home() / ".config" / "chaos" / "chobolo_template.yml",
            )
            oc.save(conf, path)

        else:
            if payload.human:
                print(oc.to_yaml(conf, resolve=True))
            else:
                print(conf)
