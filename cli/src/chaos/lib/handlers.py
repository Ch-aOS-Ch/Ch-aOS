from importlib import import_module
from rich.console import Console
from rich.prompt import Confirm
from rich.text import Text
from pathlib import Path
from omegaconf import DictConfig, OmegaConf

import subprocess
import math
import logging
import os
import sys
import shutil
import tempfile
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

def handleCreateRamble(args):
    ramble = args.target
    CONFIG_DIR = Path(os.path.expanduser("~/.local/share/chaos/ramblings"))
    if '.' in ramble:
        parts = ramble.split('.', 1)
        directory = parts[0]
        if not parts[1]:
            console.print(f"[bold red]ERROR:[/] No page passed for {directory}")
            sys.exit(1)
        page = parts[1]
        baseText=f"""title: {page}
concept:
what:
why:
how:
scripts:
"""
        path = CONFIG_DIR / directory
        if not path.exists():
            path.mkdir(parents=True, exist_ok=True)
            console.print(f'[yellow]Created new journal: {directory}![/]')

        CONFIG_FILE_PATH = path / f'{page}.yml'
        try:
            f = open(CONFIG_FILE_PATH, 'x')
            f.write(baseText)
            f.close()
            console.print(f'[bold green][italic]Page {page} created![/][/] [dim]{directory}.{page}[/]')
        except FileExistsError:
            ask = console.input(f'[bold yellow]WARNING:[/] page {page} already exists!\n Do you want to go write on it? (y/N) ')
            if not ask.lower() == 'y':
                sys.exit(1)
        editor = os.getenv('EDITOR', 'nano')
        try:
            subprocess.run([editor, CONFIG_FILE_PATH], check=True)
        except subprocess.CalledProcessError as e:
            console.print(f'[bold red]ERROR: ramble editing failed: {e}')
            sys.exit(1)

    else:
        path = CONFIG_DIR/ramble
        fullPath = path/f'{ramble}.yml'
        baseText=f"""title: {ramble}
concept:
what:
why:
how:
scripts:
"""
        try:
            path.mkdir(parents=True, exist_ok=True)
            console.print(f'[bold green]Journal "{ramble}" created![/]')
            try:
                f = open(fullPath, 'x')
                f.write(baseText)
                f.close()
                console.print(f'[bold green][italic]Page {ramble} created![/][/] [dim]{ramble}.{ramble}[/]')
            except FileExistsError:
                ask = console.input(f'[bold yellow]WARNING:[/] page {ramble} already exists!\n Do you want to go write on it? (y/N) ')
                if not ask.lower() == 'y':
                    sys.exit(1)

        except FileExistsError:
            console.print(f"[yellow]Journal '{ramble}' already exists.[/]")

        editor = os.getenv('EDITOR', 'nano')
        try:
            subprocess.run([editor, fullPath], check=True)
        except subprocess.CalledProcessError as e:
            console.print(f'[bold red]ERROR: ramble editing failed: {e}')
            sys.exit(1)

    sys.exit(0)

def handleEditRamble(args):
    from rich.table import Table
    from rich.panel import Panel
    from rich.align import Align

    ramble = args.target
    CONFIG_DIR = Path(os.path.expanduser("~/.local/share/chaos/ramblings"))

    GLOBAL_CONFIG_DIR = os.path.expanduser("~/.config/chaos")
    GLOBAL_CONFIG_FILE_PATH = os.path.join(GLOBAL_CONFIG_DIR, "config.yml")
    global_config = {}
    if os.path.exists(GLOBAL_CONFIG_FILE_PATH):
        global_config = OmegaConf.load(GLOBAL_CONFIG_FILE_PATH) or OmegaConf.create()

    sops_file_override = None
    if hasattr(args, 'sops_file_override') and args.sops_file_override:
        sops_file_override = args.sops_file_override
    else:
        sops_file_override = global_config.get('sops_file')

    def edit_file(file_path):
        is_encrypted = False
        try:
            data = OmegaConf.load(file_path)
            if 'sops' in data:
                is_encrypted = True
        except Exception:
            pass

        if is_encrypted:
            if not sops_file_override:
                console.print('[bold red]ERROR:[/] This ramble appears to be encrypted, but no sops configuration was found.')
                console.print("   Provide one with '[cyan]-ss /path/to/.sops.yml[/cyan]' or set a default with '[cyan]chaos set sops /path/to/.sops.yml[/cyan]'.")
                sys.exit(1)
            try:
                subprocess.run(['sops', '--config', sops_file_override, str(file_path)], check=True)
            except FileNotFoundError:
                console.print('[bold red]ERROR:[/] The `sops` command was not found. Please install sops to edit encrypted rambles.')
                sys.exit(1)
            except subprocess.CalledProcessError as e:
                if e.returncode == 200:
                    print('')
                else:
                    console.print(f'[bold red]ERROR: Ramble editing with sops failed: {e}')
                    sys.exit(1)
        else:
            editor = os.getenv('EDITOR', 'nano')
            try:
                subprocess.run([editor, file_path], check=True)
            except FileNotFoundError:
                console.print(f'[bold red]ERROR:[/] Editor `{editor}` not found. Please set your EDITOR environment variable.')
                sys.exit(1)
            except subprocess.CalledProcessError as e:
                console.print(f'[bold red]ERROR: Ramble editing failed: {e}')
                sys.exit(1)

    if '.' in ramble:
        parts = ramble.split('.', 1)
        directory = parts[0]

        if not parts[1]:
            page = directory
        else:
            page = parts[1]

        path = CONFIG_DIR / directory
        if not path.exists():
            console.print(f'[bold red]ERROR:[/] Journal directory not found: {path}')
            sys.exit(1)

        CONFIG_FILE_PATH = path / f'{page}.yml'
        if not CONFIG_FILE_PATH.exists():
            console.print(f'[bold red]ERROR:[/] Ramble page not found: {CONFIG_FILE_PATH}')
            sys.exit(1)

        edit_file(CONFIG_FILE_PATH)
        sys.exit(0)

    path = CONFIG_DIR / ramble
    try:
        entries = sorted([f.name for f in path.iterdir() if f.is_file()])
    except FileNotFoundError:
        console.print(f"[bold red]ERROR:[/] Journal not found: {path}.")
        sys.exit(1)

    if not entries:
        console.print(f"[yellow]No pages found in the '{ramble}' journal.[/]")
        sys.exit(0)

    table = Table(show_lines=True)
    table.add_column(f'Index', style='cyan')
    table.add_column(f'Pages in {ramble}', style='green')

    for i, e in enumerate(entries, start=1):
        table.add_row(str(i), Path(e).stem)

    console.print(Align.center(Panel(table, expand=False, border_style="green", title=f'Journal: [cyan]{ramble}[/]')))
    inp = console.input("Which page do you want to edit? (index) ")

    if inp:
        try:
            indx = int(inp)
            if 1 <= indx <= len(entries):
                selected_file_name = entries[indx - 1]
                file_to_edit = path / selected_file_name
                edit_file(file_to_edit)
            else:
                raise IndexError
        except (IndexError, ValueError):
            console.print(f"[bold red]ERROR:[/] Invalid index: '{inp}'")
            sys.exit(1)
        sys.exit(0)
    else:
        console.print("No page selected. Exiting.")
        sys.exit(0)

def handleEncryptRamble(args):
    console_err = Console(stderr=True)
    GLOBAL_CONFIG_DIR = os.path.expanduser("~/.config/chaos")
    GLOBAL_CONFIG_FILE_PATH = os.path.join(GLOBAL_CONFIG_DIR, "config.yml")
    global_config = {}
    if os.path.exists(GLOBAL_CONFIG_FILE_PATH):
        global_config = OmegaConf.load(GLOBAL_CONFIG_FILE_PATH) or OmegaConf.create()

    sops_file_override = None
    if hasattr(args, 'sops_file_override') and args.sops_file_override:
        sops_file_override = args.sops_file_override
    else:
        sops_file_override = global_config.get('sops_file')

    if not sops_file_override:
        console.print('[bold red]ERROR:[/] You need a sops configuration for encryption to work.')
        console.print("   Provide one with '[cyan]-ss /path/to/.sops.yml[/cyan]' or set a default with '[cyan]chaos set sops /path/to/.sops.yml[/cyan]'.")
        sys.exit(1)

    ramble = args.target
    keys = args.keys or []
    CONFIG_DIR = Path(os.path.expanduser("~/.local/share/chaos/ramblings"))

    if not '.' in ramble:
        console.print('[bold red]ERROR:[/] You must pass a specific page to be encrypted (e.g., diary.page).')
        sys.exit(1)

    parts = ramble.split('.', 1)
    directory = parts[0]
    page = parts[1]

    path = CONFIG_DIR / directory
    fullPath = path / f'{page}.yml'

    if not fullPath.exists():
        console.print(f"[bold red]ERROR:[/] Ramble page not found: {fullPath}")
        sys.exit(1)

    try:
        data = OmegaConf.load(fullPath)
    except Exception as e:
        console.print(f'[bold red]ERROR:[/] Could not read ramble file: {e}')
        sys.exit(1)

    keysInData = data.keys()
    baseKeys = ['title', 'concept', 'sops']

    if not keys:
        keys = [str(key) for key in keysInData if key not in baseKeys]

    if not keys:
        console.print('[yellow]No new keys to encrypt. Exiting.[/]')
        sys.exit(0)

    joinKeys = '|'.join(keys)
    regex = f"^({joinKeys})$"
    console.print(f'[italic][yellow]Encrypting these keys:[/][cyan] {keys}[/][/]')

    if 'sops' in data:
        try:
            result = subprocess.run(['sops', '--config', sops_file_override, '-d', str(fullPath)], capture_output=True, text=True, check=True)
            with tempfile.NamedTemporaryFile(mode='w', delete=False) as tmp:
                tmp.write(result.stdout)
                tmpPath=tmp.name
        except FileNotFoundError:
            console.print('[bold red]ERROR:[/] The `sops` command was not found. Please install sops to edit encrypted rambles.')
            sys.exit(1)
        except subprocess.CalledProcessError as e:
            console.print(f'[bold red]ERROR: Ramble decryption with sops failed: {e}')
            sys.exit(1)

        try:
            subprocess.run(
                [
                    'sops',
                    '--config', sops_file_override,
                    '--encrypt',
                    '--in-place',
                    '--encrypted-regex', regex,
                    str(tmpPath)
                ],
                check=True
            )
            shutil.move(tmpPath, fullPath)
            console.print(f"[bold green]Successfully encrypted keys in {ramble}[/]")
        except FileNotFoundError:
            console.print('[bold red]ERROR:[/] The `sops` command was not found. Please install sops to encrypt rambles.')
            sys.exit(1)
        except subprocess.CalledProcessError as e:
            console.print(f'[bold red]ERROR: Ramble encryption failed: {e}')
            sys.exit(1)

    else:
        try:
            subprocess.run(
                [
                    'sops',
                    '--config', sops_file_override,
                    '--encrypt',
                    '--in-place',
                    '--encrypted-regex', regex,
                    str(fullPath)
                ],
                check=True
            )
            console.print(f"[bold green]Successfully encrypted keys in {ramble}[/]")
        except FileNotFoundError:
            console.print('[bold red]ERROR:[/] The `sops` command was not found. Please install sops to encrypt rambles.')
            sys.exit(1)
        except subprocess.CalledProcessError as e:
            console.print(f'[bold red]ERROR: Ramble encryption failed: {e}')
            sys.exit(1)

    sys.exit(0)

def _read_ramble_content(ramble_path, sops_config):
    if not ramble_path.exists():
        console.print(f'[bold red]ERROR:[/] Ramble page not found: {ramble_path}')
        return

    ramble_data = None
    try:
        data = OmegaConf.load(ramble_path)
        is_encrypted = 'sops' in data

        if is_encrypted:
            if not sops_config:
                console.print('[bold red]ERROR:[/] This ramble appears to be encrypted, but no sops configuration was found.')
                console.print("   Provide one with '[cyan]-ss /path/to/.sops.yml[/cyan]' or set a default with '[cyan]chaos set sops /path/to/.sops.yml[/cyan]'.")
                return None, None

            result = subprocess.run(
                ['sops', '--config', sops_config, '-d', str(ramble_path)],
                capture_output=True, text=True, check=True
            )
            text = result.stdout
            ramble_data = OmegaConf.create(text)
            return ramble_data, text
        else:
            ramble_data = data
            with open(ramble_path, 'r') as f:
                text = f.read()
            return ramble_data, text

    except subprocess.CalledProcessError as e:
        console.print(f'[bold red]ERROR: Ramble decryption with sops failed.[/]\n{e.stderr}')
        return None, None
    except FileNotFoundError:
        console.print(f"[bold red]ERROR:[/] File not found or `sops` command not found. Please check the path and that sops is installed.")
        return None, None
    except Exception as e:
        console.print(f'[bold red]ERROR:[/] Could not read or parse ramble file: {ramble_path}\n{e}')
        return None, None

def _print_ramble(ramble_path, sops_config, target_name):
    from rich.panel import Panel
    from rich.syntax import Syntax
    from rich.markdown import Markdown
    from rich.padding import Padding
    from rich.console import Group
    from rich.align import Align

    ramble_data, _ = _read_ramble_content(ramble_path, sops_config)

    renderables = []
    standard_keys = {'title', 'concept', 'what', 'why', 'how', 'scripts', 'sops'}

    if ramble_data is not None:
        if 'concept' in ramble_data and ramble_data.concept:
            renderables.append(Markdown(f"# Concept: {ramble_data.concept}"))
            renderables.append(Text("\n"))
        if 'what' in ramble_data and ramble_data.what:
            renderables.append(Markdown(f"**What is it?**"))
            renderables.append(Padding.indent(Markdown(ramble_data.what), 4))
            renderables.append(Text("\n"))
        if 'why' in ramble_data and ramble_data.why:
            renderables.append(Markdown(f"**Why use it?**"))
            renderables.append(Padding.indent(Markdown(ramble_data.why), 4))
            renderables.append(Text("\n"))
        if 'how' in ramble_data and ramble_data.how:
            renderables.append(Markdown(f"**How it works:**"))
            renderables.append(Padding.indent(Markdown(ramble_data.how), 4))
            renderables.append(Text("\n"))

        scripts = ramble_data.get('scripts')
        if scripts:
            renderables.append(Markdown("**Scripts:**"))
            if isinstance(scripts, DictConfig):
                knownLangs = ['python', 'c', 'java', 'javascript', 'rust', 'bash', 'go', 'c++', 'json']
                for lang, code in scripts.items():
                    if lang in knownLangs and code:
                        renderables.append(Padding.indent(Syntax(code, lang, line_numbers=True, theme="ansi_dark"), 5))
            else:
                renderables.append(Padding.indent(Syntax(scripts, "bash", line_numbers=True, theme="monokai"), 5))
            renderables.append(Text("\n"))

        other_keys = [k for k in ramble_data.keys() if k not in standard_keys]
        if other_keys:
            for key in other_keys:
                renderables.append(Markdown(f"**{key.replace('_', ' ').title()}:**"))
                content = ramble_data.get(key)

                formatted_content = ""
                if content is None:
                    formatted_content = "null"
                elif isinstance(content, str):
                    formatted_content = content
                elif isinstance(content, (dict, list)): # OmegaConf containers are instances of dict/list
                    formatted_content = OmegaConf.to_yaml(content).strip()
                else:
                    formatted_content = str(content)

                renderables.append(Padding.indent(Markdown(formatted_content), 5))
                renderables.append(Text("\n"))

        title = ramble_data.get('title', target_name)
        console.print(
            Align.center(
                Panel(
                    Group(*renderables),
                    title=f"[bold green]Ramble for '{title}'[/]",
                    border_style="green",
                    expand=False,
                    width=100
                )
            )
        )
    else:
        console.print("ERROR: ramble_data returned None.")

def _process_ramble_target(target, sops_file_override):
    from rich.table import Table
    from rich.panel import Panel
    from rich.align import Align

    CONFIG_DIR = Path(os.path.expanduser("~/.local/share/chaos/ramblings"))
    parts = target.split('.', 1)
    journal = parts[0]
    path = CONFIG_DIR / journal

    is_list_request = (len(parts) > 1 and parts[1] == 'list') or len(parts) == 1

    if is_list_request:
        try:
            entries = sorted([f.name for f in path.iterdir() if f.is_file()])
            if not entries:
                console.print(f"[yellow]No pages found in the '{journal}' journal.[/]")
                return

            table = Table(show_lines=True)
            table.add_column(f'Index', style='cyan')
            table.add_column(f'Pages in {journal}', style='green')
            for i, e in enumerate(entries, start=1):
                table.add_row(str(i), Path(e).stem)
            console.print(Align.center(Panel(table, expand=False, border_style="green", title=f'Journal: [cyan]{journal}[/]')))

            inp = console.input("Which page do you want to read? (index) ")
            if not inp:
                console.print("No page selected. Exiting.")
                return

            try:
                indx = int(inp)
                if 1 <= indx <= len(entries):
                    selected_file_name = entries[indx - 1]
                    file_to_read = path / selected_file_name
                    _print_ramble(file_to_read, sops_file_override, Path(selected_file_name).stem)
                else:
                    raise IndexError
            except (IndexError, ValueError):
                console.print(f"[bold red]ERROR:[/] Invalid index: '{inp}'")
                return

        except FileNotFoundError:
            console.print(f"[bold red]ERROR:[/] Journal not found: {path}.")
            return

    else:
        page = parts[1]
        if not page:
             console.print(f"[bold red]ERROR:[/] No page passed for journal '{journal}'.")
             return
        full_path = path / f'{page}.yml'
        _print_ramble(full_path, sops_file_override, target)

def handleReadRamble(args):
    GLOBAL_CONFIG_DIR = os.path.expanduser("~/.config/chaos")
    GLOBAL_CONFIG_FILE_PATH = os.path.join(GLOBAL_CONFIG_DIR, "config.yml")
    global_config = {}
    if os.path.exists(GLOBAL_CONFIG_FILE_PATH):
        global_config = OmegaConf.load(GLOBAL_CONFIG_FILE_PATH) or OmegaConf.create()

    sops_file_override = None
    if hasattr(args, 'sops_file_override') and args.sops_file_override:
        sops_file_override = args.sops_file_override
    else:
        sops_file_override = global_config.get('sops_file')

    for target in args.targets:
        _process_ramble_target(target, sops_file_override)

    sys.exit(0)

def handleFindRamble(args):
    from rich.table import Table
    from rich.panel import Panel
    from rich.align import Align
    from itertools import zip_longest

    RAMBLE_DIR = Path(os.path.expanduser("~/.local/share/chaos/ramblings"))
    search_term = getattr(args, 'find_term', None)
    required_tag = getattr(args, 'tag', None)
    results = []


    GLOBAL_CONFIG_DIR = os.path.expanduser("~/.config/chaos")
    GLOBAL_CONFIG_FILE_PATH = os.path.join(GLOBAL_CONFIG_DIR, "config.yml")
    global_config = {}

    if os.path.exists(GLOBAL_CONFIG_FILE_PATH):
        global_config = OmegaConf.load(GLOBAL_CONFIG_FILE_PATH) or OmegaConf.create()

    sops_file_override = None

    if hasattr(args, 'sops_file_override') and args.sops_file_override:
        sops_file_override = args.sops_file_override
    else:
        sops_file_override = global_config.get('sops_file')


    if search_term or required_tag:
        for ramble_file in RAMBLE_DIR.rglob("*.yml"):
            data, text = _read_ramble_content(ramble_file, sops_file_override)

            if data is None or text is None:
                continue

            if required_tag:
                tags = data.get('tags', [])
                if required_tag not in tags:
                    continue

            if search_term:
                if search_term.lower() not in text.lower():
                    continue

            ramble = ramble_file.parent.name
            page = ramble_file.stem
            results.append(f"{ramble}.{page}")
    else:
        for ramble_file in RAMBLE_DIR.rglob('*.yml'):
            ramble = ramble_file.parent.name
            page = ramble_file.stem
            results.append(f"{ramble}.{page}")

    if not results:
        console.print("Could not find any rambles.")
        return

    items = sorted(results)
    num_items = len(results)
    max_rows = 4

    if num_items < 5:
        table = Table(show_lines=True, expand=False, show_header=False)
        table.add_column(justify="center")

        for item in items:
            table.add_row(f"[italic][cyan]{item}[/][/]")

        console.print(Align.center(Panel(Align.center(table), border_style="green", expand=False, title=f"[italic][green]Found ramblings:[/][/]")), justify="center")
    else:
        num_columns = math.ceil(num_items / max_rows)

        table = Table(
            show_lines=True,
            expand=False,
            show_header=False
        )

        for _ in range(num_columns):
            table.add_column(justify="center")

        chunks = [items[i:i + max_rows] for i in range(0, num_items, max_rows)]
        transposed_items = zip_longest(*chunks, fillvalue="")

        for row_data in transposed_items:
            styled_row = [f"[cyan][italic]{item}[/][/]" if item else "" for item in row_data]
            table.add_row(*styled_row)

        console.print(Align.center(Panel(Align.center(table), border_style="green", expand=False, title=f"[italic][green]Found ramblings:[/][/]")), justify="center")

def handleMoveRamble(args):
    RAMBLE_DIR = Path(os.path.expanduser("~/.local/share/chaos/ramblings"))
    old = args.old
    new = args.new

    old_is_dir = '.' not in old
    new_is_dir = '.' not in new

    # Determine source path
    if old_is_dir:
        source_path = RAMBLE_DIR / old
    else:
        try:
            old_journal, old_page = old.split('.', 1)
            source_path = RAMBLE_DIR / old_journal / f"{old_page}.yml"
        except ValueError:
            console.print(f"[bold red]ERROR:[/] Invalid source format: '{old}'")
            sys.exit(1)

    # Determine destination paths
    if new_is_dir:
        dest_dir_path = RAMBLE_DIR / new
    else:
        try:
            new_journal, new_page = new.split('.', 1)
            dest_dir_path = RAMBLE_DIR / new_journal
            dest_file_path = dest_dir_path / f"{new_page}.yml"
        except ValueError:
            console.print(f"[bold red]ERROR:[/] Invalid destination format: '{new}'")
            sys.exit(1)


    # Case 1: Move/Rename directory (ramble1 -> ramble2)
    if old_is_dir and new_is_dir:
        if not source_path.is_dir():
            console.print(f"[bold red]ERROR:[/] No such journal (directory): {source_path}")
            sys.exit(1)
        if dest_dir_path.exists():
            console.print(f"[bold red]ERROR:[/] Destination journal (directory) already exists: {dest_dir_path}")
            sys.exit(1)

        shutil.move(str(source_path), str(dest_dir_path))
        console.print(f"[green]Successfully moved journal '{old}' to '{new}'[/]")
        sys.exit(0)

    # Case 2: Move/Rename file (ramble1.page1 -> ramble2.page2)
    if not old_is_dir and not new_is_dir:
        if not source_path.is_file():
            console.print(f"[bold red]ERROR:[/] No such page (file): {source_path}")
            sys.exit(1)
        if dest_file_path.exists():
            console.print(f"[bold red]ERROR:[/] Destination page (file) already exists: {dest_file_path}")
            sys.exit(1)

        dest_file_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(str(source_path), str(dest_file_path))
        console.print(f"[green]Successfully moved page '{old}' to '{new}'[/]")
        sys.exit(0)

    # Case 3: Move directory to file (ramble1 -> ramble2.page2) -> FORBIDDEN
    if old_is_dir and not new_is_dir:
        console.print("[bold red]ERROR:[/] system cannot move a directory to a singular file")
        sys.exit(1)

    # Case 4: Move file to directory (ramble1.page1 -> ramble2)
    if not old_is_dir and new_is_dir:
        if not source_path.is_file():
            console.print(f"[bold red]ERROR:[/] No such page (file): {source_path}")
            sys.exit(1)

        final_dest_file = dest_dir_path / source_path.name

        if final_dest_file.exists():
            console.print(f"[bold red]ERROR:[/] Page (file) '{source_path.name}' already exists in journal '{new}'")
            sys.exit(1)

        dest_dir_path.mkdir(parents=True, exist_ok=True)
        shutil.move(str(source_path), str(final_dest_file))
        new_ramble_name = f"{new}.{source_path.stem}"
        console.print(f"[green]Successfully moved page '{old}' to '{new_ramble_name}'[/]")
        sys.exit(0)

    console.print("[bold red]An unknown error occurred during the move operation.[/]")
    sys.exit(1)

def handleDelRamble(args):
    RAMBLE_DIR = Path(os.path.expanduser("~/.local/share/chaos/ramblings"))
    ramble = args.ramble

    if '.' in ramble:
        ramblePath = RAMBLE_DIR / ramble.replace('.', '/')
        rambleFile = Path(str(ramblePath) + ".yml")

        if not rambleFile.exists():
            console.print(f"[bold red]ERROR:[/] {rambleFile} does not exist.")
            sys.exit(1)

        confirmation = Confirm.ask(f"Are you [red][italic]sure[/][/] you want to delete {ramble}?", default=False)
        if confirmation:
            console.print(f"[bold red]Removing {ramble}.[/]")
            os.remove(rambleFile)
            sys.exit(0)
        console.print("[green]Alright![/] Aborting.")
    else:
        ramblePath = RAMBLE_DIR / ramble

        if not ramblePath.exists():
            console.print(f"[bold red]ERROR:[/] {ramblePath} does not exist.")
            sys.exit(1)

        confirmation = Confirm.ask(f"Are you [red][italic]sure[/][/] you want to delete {ramble}?", default=False)
        if confirmation:
            console.print(f"[bold red]Removing {ramble}.[/]")
            shutil.rmtree(ramblePath)
            sys.exit(0)
        console.print("[green]Alright![/] Aborting.")
