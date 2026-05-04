import sys


def render_explanation(payload, result_data):
    import json
    import subprocess

    from omegaconf import OmegaConf
    from rich.align import Align
    from rich.console import Console, Group
    from rich.markdown import Markdown
    from rich.padding import Padding
    from rich.pager import Pager
    from rich.panel import Panel
    from rich.syntax import Syntax
    from rich.table import Table
    from rich.text import Text
    from rich.tree import Tree

    class ChaosPager(Pager):
        def __init__(self, command=["less", "-RXL"]):
            self.command = command

        def show(self, renderables):
            with subprocess.Popen(
                self.command,
                stdin=subprocess.PIPE,
                text=True,
            ) as proc:
                proc.communicate(input=renderables)

    pager = ChaosPager(command=["less", "-RXL"])

    console = Console()

    DETAIL_LEVELS = {
        "basic": ["concept", "what", "why", "examples", "security"],
        "intermediate": [
            "what",
            "why",
            "how",
            "commands",
            "equivalent",
            "examples",
            "security",
        ],
        "advanced": [
            "concept",
            "what",
            "why",
            "how",
            "technical",
            "commands",
            "files",
            "security",
            "equivalent",
            "examples",
            "validation",
            "learn_more",
        ],
    }

    keysToShow = DETAIL_LEVELS.get(payload.details, DETAIL_LEVELS["basic"])

    for topic, data in result_data.items():
        if data["type"] == "list":
            role = data["role"]
            exp_list = data["sub_topics"]

            if payload.no_pretty:
                print(json.dumps(exp_list, indent=2))
                continue

            table = Table(show_lines=True, width=40)
            table.add_column(f"{role}", justify="center")
            for m in exp_list:
                table.add_row(f"[cyan][italic]{m}[/][/]")
            console.print(
                Align.center(
                    Panel(
                        table,
                        border_style="green",
                        expand=False,
                        title=f"[italic][bold green]Available subtopics for[/] [bold magenta]{role}[/bold magenta][/]:",
                    )
                )
            )

        elif data["type"] == "explanation":
            explanation = data["content"]
            if payload.no_pretty:
                if payload.json:
                    print(
                        json.dumps(
                            OmegaConf.to_container(
                                OmegaConf.create(explanation), resolve=True
                            ),
                            indent=2,
                        )
                    )
                else:
                    print(OmegaConf.to_yaml(OmegaConf.create(explanation)))
                continue

            explanation_renderables = []

            if "concept" in keysToShow and explanation.get("concept"):
                explanation_renderables.append(
                    Markdown(f"# Concept: {explanation['concept']}")
                )
                explanation_renderables.append(Text("\n"))

            if "what" in keysToShow and explanation.get("what"):
                explanation_renderables.append(Markdown("**What does it do?**"))
                explanation_renderables.append(
                    Padding.indent(
                        Markdown(
                            explanation["what"],
                        ),
                        5,
                    )
                )
                explanation_renderables.append(Text("\n"))

            if "technical" in keysToShow and explanation.get("technical"):
                explanation_renderables.append(Markdown("**Technical details:**"))
                explanation_renderables.append(
                    Padding.indent(Markdown(explanation["technical"]), 5)
                )
                explanation_renderables.append(Text("\n"))

            if "why" in keysToShow and explanation.get("why"):
                explanation_renderables.append(Markdown("**Why use it:**"))
                explanation_renderables.append(
                    Padding.indent(Markdown(explanation["why"]), 5)
                )
                explanation_renderables.append(Text("\n"))

            if "how" in keysToShow and explanation.get("how"):
                explanation_renderables.append(Markdown("**How it works:**"))
                explanation_renderables.append(
                    Padding.indent(Markdown(explanation["how"]), 5)
                )
                explanation_renderables.append(Text("\n"))

            if "validation" in keysToShow and explanation.get("validation"):
                explanation_renderables.append(Markdown("**Validation:**"))
                explanation_renderables.append(
                    Padding.indent(
                        Syntax(
                            explanation["validation"],
                            "bash",
                            line_numbers=True,
                            word_wrap=True,
                        ),
                        5,
                    )
                )
                explanation_renderables.append(Text("\n"))

            examples = explanation.get("examples", [])
            if "examples" in keysToShow and len(examples) > 0:
                explanation_renderables.append(Markdown("**Examples:**"))
                for ex in examples:
                    if "yaml" in ex:
                        explanation_renderables.append(
                            Padding.indent(
                                Syntax(
                                    ex["yaml"],
                                    "yaml",
                                    line_numbers=True,
                                    word_wrap=True,
                                ),
                                5,
                            )
                        )
                explanation_renderables.append(Text("\n"))

            if "equivalent" in keysToShow and explanation.get("equivalent"):
                explanation_renderables.append(Markdown("**Equivalent script:**"))
                equivalent = explanation["equivalent"]
                if isinstance(equivalent, list):
                    for cmd in equivalent:
                        explanation_renderables.append(
                            Padding.indent(
                                Syntax(cmd, "bash", line_numbers=True, word_wrap=True),
                                5,
                            )
                        )
                else:
                    explanation_renderables.append(
                        Padding.indent(
                            Syntax(
                                equivalent, "bash", line_numbers=True, word_wrap=True
                            ),
                            5,
                        )
                    )
                explanation_renderables.append(Text("\n"))

            files = explanation.get("files", [])
            if "files" in keysToShow and files:
                tree = Tree(
                    "[bold]Related files[/]",
                )
                for f in files:
                    tree.add(f"[green]{f}[/green]")
                explanation_renderables.append(tree)
                explanation_renderables.append(Text("\n"))

            commands = explanation.get("commands", [])
            if "commands" in keysToShow and commands:
                tree = Tree("[bold]Related Commands:[/]")
                for command in commands:
                    tree.add(f"[cyan]{command}[/cyan]")
                explanation_renderables.append(tree)
                explanation_renderables.append(Text("\n"))

            learn_more = explanation.get("learn_more", [])
            if "learn_more" in keysToShow and learn_more:
                tree = Tree("[bold]Learn more[/]")
                for item in learn_more:
                    tree.add(f"[blue]{item}[/blue]")
                explanation_renderables.append(tree)
                explanation_renderables.append(Text("\n"))

            if "security" in keysToShow and explanation.get("security"):
                explanation_renderables.append(
                    Align.center(
                        Panel(
                            Markdown(explanation["security"]),
                            title="[bold yellow]Security considerations[/]",
                            border_style="yellow",
                            expand=False,
                        )
                    )
                )
                explanation_renderables.append(Text("\n"))

            with console.pager(pager=pager, styles=True):
                console.print(
                    Align.center(
                        Panel(
                            Group(*explanation_renderables),
                            title=f"[bold green]Explanation for topic '{topic}'[/] ([italic]{payload.details}-{payload.complexity}[/])",
                            border_style="green",
                            expand=False,
                            width=80 if len(explanation_renderables) > 1 else None,
                        )
                    )
                )


def handleExplain(args):  # noqa: C901
    if args.topics:
        from rich.console import Console

        from chaos.lib.args.dataclasses import ExplainPayload
        from chaos.lib.explain import handleExplain as libHandleExplain
        from chaos.lib.plugDiscovery import get_plugins

        console = Console()

        payload = ExplainPayload(
            topics=args.topics,
            complexity=args.complexity,
            details=args.details,
            no_pretty=args.no_pretty,
            json=args.json,
        )

        EXPLANATIONS = get_plugins(args.update_plugins)[2]

        result = libHandleExplain(payload, EXPLANATIONS)

        if result.data:
            render_explanation(payload, result.data)

        if result.error:
            for err in result.error:
                if err.startswith("Available sub-topics for"):
                    console.print(f"[yellow]{err}[/yellow]")
                else:
                    console.print(f"[bold red]ERROR:[/] {err}")

            if not result.success:
                sys.exit(1)
    else:
        print("No explanation passed.")
