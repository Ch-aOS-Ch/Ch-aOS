import os
import sys


def handleInit(args):
    from rich.console import Console

    console = Console()
    try:
        from chaos.lib.inits import initChobolo, initSecrets

        match args.init_command:
            case "chobolo":
                from omegaconf import OmegaConf as oc

                from chaos.lib.plugDiscovery import get_plugins

                keys = get_plugins(args.update_plugins)[3]
                conf = initChobolo(keys)

                if not args.template:
                    path = os.path.expanduser("~/.config/chaos/ch-obolo_template.yml")
                    oc.save(conf, path)

                else:
                    if args.human:
                        print(oc.to_yaml(conf, resolve=True))
                    else:
                        print(conf)

            case "secrets":
                initSecrets()
            case _:
                console.print("Unsupported init.")
    except (EnvironmentError, FileNotFoundError, ValueError, RuntimeError) as e:
        console.print(f"[bold red]ERROR:[/] {e}")
        sys.exit(1)
