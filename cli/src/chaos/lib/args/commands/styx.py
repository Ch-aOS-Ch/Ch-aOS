import sys


def handleStyx(args):
    from rich.console import Console

    console = Console()

    from chaos.lib.args.dataclasses import ResultPayload, StyxPayload
    from chaos.lib.styx import handle_styx

    payload = StyxPayload(
        styx_commands=args.styx_commands,
        entries=getattr(args, "entries", []),
        no_pretty=getattr(args, "no_pretty", False),
        json=getattr(args, "json", False),
    )

    result: ResultPayload = handle_styx(payload)

    if result.message:
        for msg in result.message:
            console.print(f"[green]{msg}[/]")

    if result.error:
        for err in result.error:
            if result.success:
                console.print(f"[yellow]WARNING:[/] {err}")
            else:
                console.print(f"[bold red]ERROR:[/] {err}")

    if payload.styx_commands == "list" and result.success:
        import json

        from omegaconf import OmegaConf

        output_data = result.data
        if payload.no_pretty:
            if not output_data:
                print("{}" if payload.json else "")
            elif payload.json:
                print(
                    json.dumps(
                        OmegaConf.to_container(
                            OmegaConf.create(output_data), resolve=True
                        ),
                        indent=2,
                    )
                )
            else:
                print(OmegaConf.to_yaml(OmegaConf.create(output_data)))
        else:
            if output_data:
                output = []
                for name, data in output_data.items():
                    desc = data.get("about", "No description")
                    ver = data.get("version", "unknown")
                    repo = data.get("repo", "")
                    hash_val = data.get("hash", "")

                    if not repo:
                        console.print(
                            f"[yellow]Warning: No repository URL for '{name}'.[/]"
                        )
                        continue

                    output.append(
                        f"""{name} ({ver})
┬"""
                        + "─" * (len(name) + 2 + len(ver))
                        + f"""
├─ {desc}
├─ 🔗 {repo}
╰─ 🛡️ {hash_val[:8] + "..." + hash_val[-8:] if hash_val else "No hash provided"}
"""
                    )
                if output:
                    console.print("\n\n".join(output))

    if not result.success:
        sys.exit(1)
