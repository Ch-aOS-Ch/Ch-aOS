import sys

from chaos.lib.args.dataclasses import ResultPayload


def handleTeam(args):
    from rich.console import Console

    console = Console()
    try:
        match args.team_commands:
            case "list":
                from chaos.lib.args.dataclasses import TeamListPayload
                from chaos.lib.team import listTeams

                payload = TeamListPayload(
                    company=args.company, no_pretty=args.no_pretty, json=args.json
                )

                result: ResultPayload = listTeams(payload)

                teams = result.data

                if not result.success:
                    if result.error:
                        for m in result.error:
                            console.print(f"[bold red]ERROR:[/] {m}")
                    sys.exit(1)

                if result.message:
                    for m in result.message:
                        console.print(f"[yellow]{m}[/]")

                if payload.no_pretty:
                    if payload.json:
                        import json as js

                        from omegaconf import OmegaConf

                        print(
                            js.dumps(
                                OmegaConf.to_container(OmegaConf.create(list(teams))),
                                indent=2,
                            )
                        )
                    else:
                        from omegaconf import OmegaConf

                        print(OmegaConf.to_yaml(OmegaConf.create(list(teams))))
                    return
                if teams:
                    from chaos.lib.display_utils import render_list_as_table

                    title = "[italic][green]Found teams:[/][/]"
                    render_list_as_table(list(teams), title)

            case "activate":
                from chaos.lib.args.dataclasses import TeamActivatePayload
                from chaos.lib.team import handleActivateTeam

                payload = TeamActivatePayload(path=args.path)

                result = handleActivateTeam(payload)
                if not result.success:
                    if result.error:
                        for err in result.error:
                            console.print(f"[bold red]ERROR:[/] {err}")
                    if result.message:
                        for msg in result.message:
                            console.print(f"[yellow]WARNING:[/] {msg}")
                    sys.exit(1)
                else:
                    if result.error:
                        for err in result.error:
                            console.print(f"[yellow]WARNING:[/] {err}")
                    if result.message:
                        for msg in result.message:
                            console.print(f"[green]Success:[/] {msg}")

            case "init":
                from chaos.lib.args.dataclasses import TeamInitPayload
                from chaos.lib.team import gatherInitTeam, handleInitTeam

                payload = TeamInitPayload(
                    target=args.target,
                    path=args.path,
                    i_know_what_im_doing=args.i_know_what_im_doing,
                )

                request = gatherInitTeam(payload)
                if request:
                    from rich.prompt import Confirm, Prompt

                    for field in request.fields:
                        if field.name == "confirmed":
                            if Confirm.ask(str(field.prompt), default=field.default):
                                payload.confirmed = True
                            else:
                                console.print("[yellow]Operation cancelled.[/]")
                                sys.exit(0)
                        elif field.name == "init_git":
                            payload.init_git = Confirm.ask(
                                str(field.prompt), default=field.default
                            )
                        elif field.name == "overwrite_sops":
                            if not Confirm.ask(
                                str(field.prompt), default=field.default
                            ):
                                console.print(
                                    "[yellow]Operation cancelled. Keeping existing config.[/]"
                                )
                                sys.exit(0)
                            else:
                                payload.overwrite_sops = True
                        elif field.name == "engine":
                            payload.engine = Prompt.ask(
                                str(field.prompt),
                                choices=field.choices,
                                default=field.default,
                            )
                        elif field.name == "use_vault":
                            payload.use_vault = Confirm.ask(
                                str(field.prompt), default=field.default
                            )
                        elif field.name == "continue_no_vault":
                            payload.continue_no_vault = Confirm.ask(
                                str(field.prompt), default=field.default
                            )

                result = handleInitTeam(payload)
                if not result.success:
                    if result.error:
                        for err in result.error:
                            console.print(f"[bold red]ERROR:[/] {err}")
                    sys.exit(1)
                else:
                    if result.message:
                        for msg in result.message:
                            console.print(f"[green]{msg}[/]")

            case "clone":
                from chaos.lib.args.dataclasses import TeamClonePayload
                from chaos.lib.team import handleCloneGitTeam

                payload = TeamClonePayload(target=args.target, path=args.path)

                result = handleCloneGitTeam(payload)
                if not result.success:
                    if result.error:
                        for err in result.error:
                            console.print(f"[bold red]ERROR:[/] {err}")
                    sys.exit(1)
                else:
                    if result.error:
                        for err in result.error:
                            console.print(f"[yellow]WARNING:[/] {err}")
                    if result.message:
                        for msg in result.message:
                            console.print(f"[green]Success:[/] {msg}")

            case "deactivate":
                from chaos.lib.args.dataclasses import TeamDeactivatePayload
                from chaos.lib.team import gatherDeactivateTeam, handleDeactivateTeam

                payload = TeamDeactivatePayload(company=args.company, teams=args.teams)

                request = gatherDeactivateTeam(payload)
                if request:
                    from rich.prompt import Confirm

                    for field in request.fields:
                        if field.name == "confirmed":
                            if Confirm.ask(str(field.prompt), default=field.default):
                                payload.confirmed = True
                            else:
                                console.print("[yellow]Operation cancelled.[/]")
                                sys.exit(0)

                result = handleDeactivateTeam(payload)
                if not result.success:
                    if result.error:
                        for err in result.error:
                            console.print(f"[bold red]ERROR:[/] {err}")
                    sys.exit(1)
                else:
                    if result.error:
                        for err in result.error:
                            console.print(f"[yellow]WARNING:[/] {err}")
                    if result.message:
                        for msg in result.message:
                            console.print(f"[green]{msg}[/]")

            case "prune":
                from chaos.lib.args.dataclasses import TeamPrunePayload
                from chaos.lib.team import gatherPruneTeams, handlePruneTeams

                payload = TeamPrunePayload(
                    companies=args.companies,
                    i_know_what_im_doing=args.i_know_what_im_doing,
                )

                request = gatherPruneTeams(payload)
                if request:
                    from rich.prompt import Confirm

                    for field in request.fields:
                        if field.name == "confirmed":
                            if Confirm.ask(str(field.prompt), default=field.default):
                                payload.confirmed = True
                            else:
                                console.print("[yellow]Operation cancelled.[/]")
                                sys.exit(0)

                result = handlePruneTeams(payload)
                if not result.success:
                    if result.error:
                        for err in result.error:
                            console.print(f"[bold red]ERROR:[/] {err}")
                    sys.exit(1)
                else:
                    if result.message:
                        for msg in result.message:
                            console.print(f"[green]{msg}[/]")

            case _:
                console.print("Unsupported team subcommand.")
    except (
        ValueError,
        FileNotFoundError,
        FileExistsError,
        RuntimeError,
        EnvironmentError,
    ) as e:
        console.print(f"[bold red]ERROR:[/] {e}")
        sys.exit(1)

