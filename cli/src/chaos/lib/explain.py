from importlib import import_module
from rich.text import Text
from rich.console import Console
import sys
console = Console()

def _setup_method_explain(EXPLAIN_DISPATCHER, role):
    try:
        module_name, class_name = EXPLAIN_DISPATCHER[role].split(':')
        module = import_module(module_name)
        ExplainClass = getattr(module, class_name)
        ExplainObj = ExplainClass()
    except (ImportError, AttributeError, ValueError) as e:
        console.print(f"[bold red]ERROR:[/] Could not load explanation class for role '{role}': {e}")
        sys.exit(1)
    return ExplainObj

def list_explain_subtopics(explainObj, role, console):
    from rich.table import Table
    from rich.panel import Panel
    from rich.align import Align
    manualOrder = getattr(explainObj, '_order', [])
    if manualOrder:
        available_methods = manualOrder
    else:
        available_methods = [m.replace('explain_', '') for m in dir(explainObj) if m.startswith('explain_') and m != 'explain_']
        available_methods = set(available_methods) - {role}
    table = Table(show_lines=True, width=40)
    table.add_column(f"{role}", justify="center")
    for m in available_methods:
        table.add_row(f"[cyan][italic]{m}[/][/]")
    console.print(Align.center(Panel(table, border_style="green", expand=False, title=f"[italic][bold green]Available subtopics for[/] [bold magenta]{role}[/bold magenta][/]:")))
    sys.exit(0)

"""
Another Chunker:

This function handles the 'explain' command.
It basically loads the appropriate explanation class based on the topic passed.
Then it calls the appropriate method to get the explanation data.
Then it formats and displays the explanation using rich.

The explanation data is expected to be a dictionary with various keys like 'concept', 'what', 'why', 'how', 'examples', etc.
The level of detail to show is determined by the 'details' argument (basic, intermediate, advanced).
If the sub-topic is 'list', it lists all available sub-topics for the given role.

I really should add a "--complexity" flag to extend the capability of detailing even further.
"""
def handleExplain(args, EXPLAIN_DISPATCHER):
    from rich.panel import Panel
    from rich.syntax import Syntax
    from rich.markdown import Markdown
    from rich.tree import Tree
    from rich.align import Align
    from rich.padding import Padding
    from rich.console import Group

    DETAIL_LEVELS = {
        'basic': ['concept', 'what', 'why', 'examples', 'security'],
        'intermediate': ['what', 'why', 'how', 'commands', 'equivalent', 'examples', 'security'],
        'advanced': ['concept', 'what', 'why', 'how', 'technical', 'commands', 'files', 'security', 'equivalent', 'examples', 'validation', 'learn_more']
    }

    topics = args.topics
    complexity = args.complexity
    if not isinstance(topics, list):
        topics = [topics]

    for topic in topics:
        keysToShow = DETAIL_LEVELS.get(args.details, DETAIL_LEVELS['basic'])
        parts = topic.split('.')
        role = parts[0]
        sub_topic = parts[1] if len(parts) > 1 else None

        if role in EXPLAIN_DISPATCHER:
            ExplainObj = _setup_method_explain(EXPLAIN_DISPATCHER, role)

            methodName = f"explain_{sub_topic}" if sub_topic else f"explain_{role}"

            if (sub_topic == 'list'):
                list_explain_subtopics(ExplainObj, role, console)

            if hasattr(ExplainObj, methodName):
                method = getattr(ExplainObj, methodName)
                explanation = method(complexity)

                explanation_renderables = []

                if 'concept' in keysToShow and explanation.get('concept'):
                    explanation_renderables.append(Markdown(f"# Concept: {explanation['concept']}"))
                    explanation_renderables.append(Text("\n"))

                if 'what' in keysToShow and explanation.get('what'):
                    explanation_renderables.append(Markdown(f"**What does it do?**"))
                    explanation_renderables.append(Padding.indent(Markdown(explanation['what'],), 5))
                    explanation_renderables.append(Text("\n"))

                if 'technical' in keysToShow and explanation.get('technical'):
                    explanation_renderables.append(Markdown(f"**Technical details:**"))
                    explanation_renderables.append(Padding.indent(Markdown(explanation['technical']), 5))
                    explanation_renderables.append(Text("\n"))

                if 'why' in keysToShow and explanation.get('why'):
                    explanation_renderables.append(Markdown(f"**Why use it:**"))
                    explanation_renderables.append(Padding.indent(Markdown(explanation['why']), 5))
                    explanation_renderables.append(Text("\n"))


                if 'how' in keysToShow and explanation.get('how'):
                    explanation_renderables.append(Markdown(f"**How it works:**"))
                    explanation_renderables.append(Padding.indent(Markdown(explanation['how']), 5))
                    explanation_renderables.append(Text("\n"))

                if 'validation' in keysToShow and explanation.get('validation'):
                    explanation_renderables.append(Markdown(f"**Validation:**"))
                    explanation_renderables.append(Padding.indent(Syntax(explanation['validation'], "bash", line_numbers=True), 5))
                    explanation_renderables.append(Text("\n"))

                examples = explanation.get('examples', [])
                if 'examples' in keysToShow and len(examples) > 0:
                    explanation_renderables.append(Markdown("**Examples:**"))
                    for ex in examples:
                        if 'yaml' in ex:
                            explanation_renderables.append(Padding.indent(Syntax(ex['yaml'], "yaml", line_numbers=True), 5))
                    explanation_renderables.append(Text("\n"))

                if 'equivalent' in keysToShow and explanation.get('equivalent'):
                    explanation_renderables.append(Markdown("**Equivalent script:**"))
                    equivalent = explanation['equivalent']
                    if isinstance(equivalent, list):
                        for cmd in equivalent:
                            explanation_renderables.append(Padding.indent(Syntax(cmd, "bash", line_numbers=True), 5))
                    else:
                        explanation_renderables.append(Padding.indent(Syntax(equivalent, "bash", line_numbers=True), 5))
                    explanation_renderables.append(Text("\n"))

                files = explanation.get('files', [])
                if 'files' in keysToShow and files:
                    tree = Tree("[bold]Related files[/]", )
                    for f in files:
                        tree.add(f"[green]{f}[/green]")
                    explanation_renderables.append(tree)
                    explanation_renderables.append(Text("\n"))

                commands = explanation.get('commands', [])
                if 'commands' in keysToShow and commands:
                    tree = Tree("[bold]Related Commands:[/]")
                    for command in commands:
                        tree.add(f"[cyan]{command}[/cyan]")
                    explanation_renderables.append(tree)
                    explanation_renderables.append(Text("\n"))
                learn_more = explanation.get('learn_more', [])

                if 'learn_more' in keysToShow and learn_more:
                    tree = Tree("[bold]Learn more[/]")
                    for item in learn_more:
                        tree.add(f"[blue]{item}[/blue]")
                    explanation_renderables.append(tree)
                    explanation_renderables.append(Text("\n"))

                if 'security' in keysToShow and explanation.get('security'):
                    explanation_renderables.append(Align.center(Panel(Markdown(explanation['security']), title="[bold yellow]Security considerations[/]", border_style="yellow", expand=False)))
                    explanation_renderables.append(Text("\n"))

                console.print(
                    Align.center(
                        Panel(
                            Group(*explanation_renderables),
                            title=f"[bold green]Explanation for topic '{topic}'[/] ([italic]{args.details}-{args.complexity}[/])",
                            border_style="green",
                            expand=False,
                            width=80 if len(explanation_renderables) > 1 else None,
                        )
                    )
                )

            else:
                if (sub_topic != 'list'):
                    available_methods = [m.replace('explain_', '') for m in dir(ExplainObj) if m.startswith('explain_') and m != 'explain_']
                    console.print(f"[bold red]ERROR:[/] No explanation found for sub-topic '{sub_topic}' in role '{role}'.")
                    if available_methods:
                        console.print(f"Available sub-topics for '{role}': [yellow]{available_methods}[/yellow]")
                    else:
                        console.print(f"[bold red]ERROR:[/] Poorly configured explanation module. \n(if you're a dev, make sure your module has a class with functions that simply return a dict with your needed explanations.)")
        else:
            console.print(f"[bold red]ERROR:[/] No explanation found for topic '{topic}'.")


