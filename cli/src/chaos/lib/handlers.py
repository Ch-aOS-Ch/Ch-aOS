from importlib import import_module
from typing import cast
from rich.console import Console
from rich.prompt import Confirm
from rich.text import Text
from pathlib import Path
from omegaconf import DictConfig, OmegaConf, ListConfig
import logging
import os
import getpass

console = Console()

"""
Orchestration/Explanation Handlers for Chaos CLI

I KNOW IT'S MESSY, IT'S INTENTIONAL.
Big function = easier to read flow, more explicit and less jumping around files.

+ Big Function = Big Brain (I've never said that)
"""

""" Handle verbosity levels for logging """
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

"""
OK, this is the big one.
Handles the orchestration of roles based on passed args and configurations.

First thing it does:

Discover Ch-obolo file path from args or global config.
Then it sets up the user configuration for posterior use.
Then it sets up pyinfra connection to localhost (probably will be extended to remote hosts later).

Now to the juicy part:
IF the role is HARD CODED _OR_ configured to be a secret having role, it handles accordingly, if it isn't hard coded, it asks for permission to proceed.
Then it gets the decrypted secrets and passes them to the role function.

If the role is 'packages', it determines the mode (all, native, aur) based on the tag used. (This is a bit of a hack, but works for now).

If the role is standard, it just calls the role function with common args.

The roles should be using pyinfra's add_op() function to queue operations, which are then executed in bulk at the end (unless dry run is active).
This allows for better performance and error handling.

I really should wrap this in a try/finally to ensure disconnection happens, but for now, this will do.
"""
def handleOrchestration(args, dry, ikwid, ROLES_DISPATCHER: DictConfig, ROLE_ALIASES: DictConfig = OmegaConf.create()):
    console = Console()
    console_err = Console(stderr=True)

    # ----- Ch-obolo Discovery -----
    CONFIG_DIR = os.path.expanduser("~/.config/chaos")
    CONFIG_FILE_PATH = os.path.join(CONFIG_DIR, "config.yml")
    global_config = OmegaConf.create()
    if os.path.exists(CONFIG_FILE_PATH):
        global_config = OmegaConf.load(CONFIG_FILE_PATH) or OmegaConf.create()
        global_config = cast(DictConfig, global_config)

    chobolo_path = args.chobolo or global_config.get('chobolo_file', None)
    secrets_file_override = args.secrets_file_override or global_config.get('secrets_file', None)
    sops_file_override = args.sops_file_override or global_config.get('sops_file', None)
    enabledSecPlugins = global_config.get('secret_plugins', [])
    userAliases = global_config.get('aliases', {})

    if not chobolo_path:
        raise FileNotFoundError("No Ch-obolo passed\n"
                            "   Use '[cyan]-e /path/to/file.yml[/cyan]' or configure a base Ch-obolo with '[cyan]chaos set chobolo /path/to/file.yml[/cyan]'.")

    chobolo_config = OmegaConf.load(chobolo_path)

    # -----------------------------
    # ---- Pyinfra Setup ----

    # --- Lazy import pyinfra components ---
    from pyinfra.api.inventory import Inventory
    from pyinfra.api.config import Config
    from pyinfra.api.connect import connect_all, disconnect_all
    from pyinfra.api.state import StateStage, State
    from pyinfra.api.operations import run_ops
    from pyinfra.context import ctx_state
    from pyinfra.api.exceptions import PyinfraError
    # ------------------------------------

    parallels = 0
    hosts = ["@local"]
    isFleet = False
    if hasattr(args, 'fleet') and args.fleet:
        fleet_config = chobolo_config.get('fleet')
        if not fleet_config:
            confirm = True if ikwid else Confirm.ask(f'[bold yellow]WARNING:[/] No fleet configured for chobolo file in {chobolo_path}, do you wish to continue? (will use localhost)', default=False)
            if not confirm:
                console.print('Exiting...')
                return

        parallels = fleet_config.get('parallelism', 0)
        fleet_hosts = fleet_config.get('hosts', [])

        if fleet_hosts:
            hosts = []
            container = OmegaConf.to_container(fleet_hosts, resolve=True)

            if not isinstance(container, list):
                raise ValueError(f"Fleet hosts configuration in {chobolo_path} is malformed. Expected a list of hosts.")

            for host_item in container:
                if isinstance(host_item, dict) and len(host_item) == 1:
                    hostname = list(host_item.keys())[0]
                    host_data = host_item[hostname]
                    hosts.append((hostname, host_data))

            isFleet = True

        else:
            confirm = True if ikwid else Confirm.ask(f'[bold yellow]WARNING:[/] No fleet hosts configured for chobolo file in {chobolo_path}, do you wish to continue? (will use localhost)', default=False)
            if not confirm:
                console.print('Exiting...')
                return

    if not isFleet:
        inventory = Inventory((hosts, {}))

    else:
        inventory = Inventory(hosts)

    config = Config(parallel=parallels)
    state = State(inventory, config)

    state.current_stage = StateStage.Prepare

    ctx_state.set(state)

    console.print("[bold magenta]Sudo password:[/bold magenta] ")
    config.SUDO_PASSWORD = getpass.getpass("")

    skip = ikwid

    console.print(f"Connecting to {hosts}...")
    connect_all(state)
    console.print("[bold green]Connection established.[/bold green]")

    # -----------------------------------------

    SEC_HAVING_ROLES=['users', 'secrets']
    SEC_HAVING_ROLES.extend(enabledSecPlugins)

    SEC_HAVING_ROLES = set(SEC_HAVING_ROLES)

    for a in userAliases.keys():
        if a in ROLE_ALIASES:
            console.print(f"[bold yellow]WARNING:[/] Alias {a} already exists in Aliases installed. Skipping.")
            del userAliases[a]

    if ROLE_ALIASES:
        ROLE_ALIASES.update(userAliases)

    decrypted_secrets = ()
    # --- Role orchestration ---
    try:
        for host in state.inventory.iter_activated_hosts():
            console.print(f"\n[bold]### Applying roles to {host.name} ###[/bold]")
            commonArgs = (state, host, chobolo_path, skip)
            for tag in args.tags:
                if ROLE_ALIASES:
                    normalized_tag = ROLE_ALIASES.get(tag, tag)
                else:
                    normalized_tag = tag
                if normalized_tag in ROLES_DISPATCHER:
                    if normalized_tag in SEC_HAVING_ROLES:
                        if normalized_tag in enabledSecPlugins:
                            confirm = True if skip else Confirm.ask(f"You are about to use a external plugin as Secret having plugin:\n[bold yellow]{normalized_tag}[/]\nAre you sure you want to continue?", default=False)
                            if not confirm:
                                continue
                        
                        if not decrypted_secrets:
                            decrypt = args.secrets
                            if decrypt:
                                from chaos.lib.secret_backends.utils import decrypt_secrets
                                decrypted_secrets = decrypt_secrets(
                                    secrets_file_override,
                                    sops_file_override,
                                    global_config,
                                    args
                                )

                            if not decrypted_secrets:
                                confirm = Confirm.ask(f"--secrets not passed, yet you are using a secret having role '{normalized_tag}', do you wish to decrypt and use it?", default=False)
                                if not confirm:
                                    continue

                                from chaos.lib.secret_backends.utils import decrypt_secrets
                                decrypted_secrets = decrypt_secrets(
                                    secrets_file_override,
                                    sops_file_override,
                                    global_config,
                                    args
                                )

                        if isinstance(decrypted_secrets, str):
                            secArgs = commonArgs + (decrypted_secrets,)
                        else:
                            secArgs = commonArgs + decrypted_secrets

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

                    console.print(f"\n--- '[bold blue]{normalized_tag}[/bold blue]' role finalized for {host.name}. ---\n")
                else:
                    console_err.print(f"\n[bold yellow]WARNING:[/] Unknown tag '{normalized_tag}'. Skipping.")

        if not dry:
            run_ops(state)
        else:
            console.print("[bold yellow]dry mode active, skipping.[/bold yellow]")
            
    except PyinfraError as e:
        console_err.print(f"[bold red]ERROR:[/] Pyinfra encountered an error: {e}")

    finally:
        # --- Disconnection ---
        console.print("\nDisconnecting...")
        disconnect_all(state)
        console.print("[bold green]Finalized.[/bold green]")


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
                return

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

"""
Just handles configuring the tool.
"""
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
            raise FileNotFoundError(f"ERROR: File not found in: {inputPath}")
    if hasattr(args, "secrets_file") and args.secrets_file:
        inputPath = Path(args.secrets_file)
        try:
            absolutePath = inputPath.resolve(strict=True)
            global_config.secrets_file = str(absolutePath)
            print(f"- Default secrets file set to: {args.secrets_file}")
        except FileNotFoundError:
            raise FileNotFoundError(f"ERROR: File not found in: {inputPath}")
    if hasattr(args, "sops_file") and args.sops_file:
        inputPath = Path(args.sops_file)
        try:
            absolutePath = inputPath.resolve(strict=True)
            global_config.sops_file = str(absolutePath)
            print(f"- Default sops file set to: {args.sops_file}")
        except FileNotFoundError:
            raise FileNotFoundError(f"ERROR: File not found in: {inputPath}")

    OmegaConf.save(global_config, CONFIG_FILE_PATH)
    print("Configuration saved.")
