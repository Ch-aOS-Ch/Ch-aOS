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
                    for m in result.message:
                        console.print(f"[bold red]ERROR:[/] {m}")
                    sys.exit(1)

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
                    from omegaconf import OmegaConf

                    print(OmegaConf.to_yaml(OmegaConf.create(list(teams))))
                from chaos.lib.display_utils import render_list_as_table

                title = "[italic][green]Found teams:[/][/]"
                render_list_as_table(list(teams), title)

            case "activate":
                from chaos.lib.args.dataclasses import TeamActivatePayload
                from chaos.lib.team import activateTeam

                payload = TeamActivatePayload(path=args.path)

                activateTeam(payload)
            case "init":
                from chaos.lib.args.dataclasses import TeamInitPayload
                from chaos.lib.team import initTeam

                payload = TeamInitPayload(
                    target=args.target,
                    path=args.path,
                    i_know_what_im_doing=args.i_know_what_im_doing,
                )

                initTeam(payload)
            case "clone":
                from chaos.lib.args.dataclasses import TeamClonePayload
                from chaos.lib.team import cloneGitTeam

                payload = TeamClonePayload(target=args.target, path=args.path)

                cloneGitTeam(payload)
            case "deactivate":
                from chaos.lib.args.dataclasses import TeamDeactivatePayload
                from chaos.lib.team import deactivateTeam

                payload = TeamDeactivatePayload(company=args.company, teams=args.teams)

                deactivateTeam(payload)
            case "prune":
                from chaos.lib.args.dataclasses import TeamPrunePayload
                from chaos.lib.team import pruneTeams

                payload = TeamPrunePayload(
                    companies=args.companies,
                    i_know_what_im_doing=args.i_know_what_im_doing,
                )

                pruneTeams(payload)
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
