from importlib import import_module
from rich.console import Console
from rich.text import Text
from pathlib import Path
from omegaconf import OmegaConf

import logging
import os
import sys
import getpass

console = Console()


def handleVerbose(args):
    log_level = None
    if args.verbose:
        if args.verbose == 1:
            log_level = logging.WARNING
        elif args.verbose == 2:
            log_level = logging.INFO
        elif args.verbose == 3:
            log_level = logging.DEBUG
    elif args.v == 1:
        log_level = logging.WARNING
    elif args.v == 2:
        log_level = logging.INFO
    elif args.v == 3:
        log_level = logging.DEBUG

    if log_level:
        logging.basicConfig(level=log_level, format="%(levelname)s: %(message)s")

def handleOrchestration(args, dry, ikwid, ROLES_DISPATCHER, ROLE_ALIASES=None):
    console = Console()
    console_err = Console(stderr=True)

    # ----- Ch-obolo Discovery -----
    CONFIG_DIR = os.path.expanduser("~/.config/chaos")
    CONFIG_FILE_PATH = os.path.join(CONFIG_DIR, "config.yml")
    global_config = {}
    if os.path.exists(CONFIG_FILE_PATH):
        global_config = OmegaConf.load(CONFIG_FILE_PATH) or OmegaConf.create()

    chobolo_path = args.chobolo or global_config.get('chobolo_file')
    secrets_file_override = args.secrets_file_override or global_config.get('secrets_file')
    sops_file_override = args.sops_file_override or global_config.get('sops_file')

    if not chobolo_path:
        console_err.print("[bold red]ERROR:[/] No Ch-obolo passed")
        console_err.print("   Use '[cyan]-e /path/to/file.yml[/cyan]' or configure a base Ch-obolo with '[cyan]chaos --set-chobolo /path/to/file.yml[/cyan]'.")
        sys.exit(1)

    # -----------------------------
    # ---- Pyinfra Setup ----

    # --- Lazy import pyinfra components ---
    from pyinfra.api.inventory import Inventory
    from pyinfra.api.config import Config
    from pyinfra.api.connect import connect_all, disconnect_all
    from pyinfra.api.state import StateStage, State
    from pyinfra.api.operations import run_ops
    from pyinfra.context import ctx_state
    # ------------------------------------

    hosts = ["@local"]
    inventory = Inventory((hosts, {}))
    config = Config()
    state = State(inventory, config)
    state.current_stage = StateStage.Prepare
    ctx_state.set(state)

    console.print("[bold magenta]Sudo password:[/bold magenta] ")
    config.SUDO_PASSWORD = getpass.getpass("")

    skip = ikwid

    console.print("Connecting to localhost...")
    connect_all(state)
    host = state.inventory.get_host("@local")
    console.print("[bold green]Connection established.[/bold green]")

    # -----------------------------------------

    # ----- args -----
    commonArgs = (state, host, chobolo_path, skip)
    secArgs = commonArgs + (
        secrets_file_override,
        sops_file_override
    )

    SEC_HAVING_ROLES={'users','secrets'}

    # --- Role orchestration ---
    for tag in args.tags:
        normalized_tag = ROLE_ALIASES.get(tag,tag)
        if normalized_tag in ROLES_DISPATCHER:
            if normalized_tag in SEC_HAVING_ROLES:
                ROLES_DISPATCHER[normalized_tag](*secArgs)
            elif normalized_tag == 'packages':
                mode = ''
                if tag in ['allPkgs', 'packages', 'pkgs']:
                    mode = 'all'
                elif tag == 'natPkgs':
                    mode = 'native'
                elif tag == 'aurPkgs':
                    mode = 'aur'

                if mode:
                    pkgArgs = commonArgs + (mode,)
                    ROLES_DISPATCHER[normalized_tag](*pkgArgs)
                else:
                    console_err.print(f"\n[bold yellow]WARNING:[/] Could not determine a mode for tag '{tag}'. Skipping.")
            else:
                ROLES_DISPATCHER[normalized_tag](*commonArgs)

            console.print(f"\n--- '[bold blue]{normalized_tag}[/bold blue]' role finalized. ---\n")
        else:
            console_err.print(f"\n[bold yellow]WARNING:[/] Unknown tag '{normalized_tag}'. Skipping.")

    if not dry:
        run_ops(state)
    else:
        console.print("[bold yellow]dry mode active, skipping.[/bold yellow]")

    # --- Disconnection ---
    console.print("\nDisconnecting...")
    disconnect_all(state)
    console.print("[bold green]Finalized.[/bold green]")

def handleExplain(args, EXPLAIN_DISPATCHER):
    from rich.panel import Panel
    from rich.syntax import Syntax
    from rich.markdown import Markdown
    from rich.table import Table
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
    if not isinstance(topics, list):
        topics = [topics]

    for topic in topics:
        keysToShow = DETAIL_LEVELS.get(args.details, DETAIL_LEVELS['basic'])
        parts = topic.split('.')
        role = parts[0]
        sub_topic = parts[1] if len(parts) > 1 else None

        if role in EXPLAIN_DISPATCHER:
            try:
                module_name, class_name = EXPLAIN_DISPATCHER[role].split(':')
                module = import_module(module_name)
                ExplainClass = getattr(module, class_name)
                explainObj = ExplainClass()
            except (ImportError, AttributeError, ValueError) as e:
                console.print(f"[bold red]ERROR:[/] Could not load explanation class for role '{role}': {e}")
                continue

            methodName = f"explain_{sub_topic}" if sub_topic else f"explain_{role}"

            if (sub_topic == 'list'):
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

            if hasattr(explainObj, methodName):
                method = getattr(explainObj, methodName)
                explanation = method()


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
                            title=f"[bold green]Explanation for topic '{topic}'[/] ([italic]{args.details}[/])",
                            border_style="green",
                            expand=False,
                            width=80 if len(explanation_renderables) > 1 else None,
                        )
                    )
                )

            else:
                if (sub_topic != 'list'):
                    available_methods = [m.replace('explain_', '') for m in dir(explainObj) if m.startswith('explain_') and m != 'explain_']
                    console.print(f"[bold red]ERROR:[/] No explanation found for sub-topic '{sub_topic}' in role '{role}'.")
                    if available_methods:
                        console.print(f"Available sub-topics for '{role}': [yellow]{available_methods}[/yellow]")
                    else:
                        console.print(f"[bold red]ERROR:[/] Poorly configured explanation module. \n(if you're a dev, make sure your module has a class with functions that simply return a dict with your needed explanations.)")
        else:
            console.print(f"[bold red]ERROR:[/] No explanation found for topic '{topic}'.")

def setMode(args):
    CONFIG_DIR = os.path.expanduser("~/.config/chaos")
    CONFIG_FILE_PATH = os.path.join(CONFIG_DIR, "config.yml")

    print(f"Saving configuration to {CONFIG_FILE_PATH}...")

    os.makedirs(CONFIG_DIR, exist_ok=True)

    if os.path.exists(CONFIG_FILE_PATH):
        global_config = OmegaConf.load(CONFIG_FILE_PATH)
    else:
        global_config = OmegaConf.create()

    if hasattr(args, "chobolo_file") and args.chobolo_file:
        inputPath = Path(args.chobolo_file)
        try:
            absolutePath = inputPath.resolve(strict=True)
            global_config.chobolo_file = str(absolutePath)
            print(f"- Default Ch-obolo set to: {args.chobolo_file}")
        except FileNotFoundError:
            print(f"ERROR: File not found in: {inputPath}", file=sys.stderr)
            sys.exit(1)
    if hasattr(args, "secrets_file") and args.secrets_file:
        inputPath = Path(args.secrets_file)
        try:
            absolutePath = inputPath.resolve(strict=True)
            global_config.secrets_file = str(absolutePath)
            print(f"- Default secrets file set to: {args.secrets_file}")
        except FileNotFoundError:
            print(f"ERROR: File not found in: {inputPath}", file=sys.stderr)
            sys.exit(1)
    if hasattr(args, "sops_file") and args.sops_file:
        inputPath = Path(args.sops_file)
        try:
            absolutePath = inputPath.resolve(strict=True)
            global_config.sops_file = str(absolutePath)
            print(f"- Default sops file set to: {args.sops_file}")
        except FileNotFoundError:
            print(f"ERROR: File not found in: {inputPath}", file=sys.stderr)
            sys.exit(1)

    OmegaConf.save(global_config, CONFIG_FILE_PATH)
    print("Configuration saved.")
