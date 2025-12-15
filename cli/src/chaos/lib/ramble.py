from rich.prompt import Confirm
from rich.console import Console
from omegaconf import DictConfig, OmegaConf
from pathlib import Path
from rich.text import Text
import subprocess
import math
import shutil
import tempfile
import os
import sys

console = Console()

def _get_ramble_dir(team: str = None) -> Path:
    """Gets the ramble directory, considering the team if provided."""
    if team:
        if ".." in team or team.startswith("/"):
             console.print(f"[bold red]ERROR:[/] Invalid team name '{team}'.")
             sys.exit(1)
        team_ramble_path = Path(os.path.expanduser(f"~/.local/share/chaos/teams/{team}/ramblings"))
        if not team_ramble_path.exists():
            console.print(f"[bold red]ERROR:[/] Team ramble directory for '{team}' not found at {team_ramble_path}.")
            sys.exit(1)
        return team_ramble_path
    return Path(os.path.expanduser("~/.local/share/chaos/ramblings"))

def is_safe_path(target_path: Path, team) -> bool:
    """
    Valida se um objeto Path alvo está contido de forma segura dentro do diretório base de ramblings.
    Esta é a verificação de segurança principal contra Path Traversal.
    """
    try:
        base_dir = _get_ramble_dir(team).resolve(strict=False)
        resolved_target = target_path.resolve(strict=False)

        if not str(resolved_target).startswith(str(base_dir)):
            console.print("[bold red]ERROR:[/] Path traversal detected. Aborting.[/]")
            return False
        return True
    except FileNotFoundError:
        console.print(f"[bold red]ERROR:[/] Directory not found.")
        return False
    except Exception as e:
        console.print(f"[bold red]ERROR:[/] Secure validation failed: {e}")
        return False

def _read_ramble_content(ramble_path, sops_config, team):
    if not is_safe_path(ramble_path, team):
        sys.exit(1)

    if not ramble_path.exists():
        console.print(f'[bold red]ERROR:[/] Ramble page not found: {ramble_path}')
        sys.exit(1)

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

def _print_ramble(ramble_path, sops_config, target_name, team):
    from rich.panel import Panel
    from rich.syntax import Syntax
    from rich.markdown import Markdown
    from rich.padding import Padding
    from rich.console import Group
    from rich.align import Align

    ramble_data, _ = _read_ramble_content(ramble_path, sops_config, team)

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
                elif isinstance(content, (dict, list)):
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

def _process_ramble_target(target, sops_file_override, team):
    from rich.table import Table
    from rich.panel import Panel
    from rich.align import Align

    if ".." in target or "/" in target:
        console.print(f"[bold red]ERROR:[/] Invalid format for ramble.")
        return

    CONFIG_DIR = _get_ramble_dir(team)
    parts = target.split('.', 1)
    journal = parts[0]
    path = CONFIG_DIR / journal

    is_list_request = (len(parts) > 1 and parts[1] == 'list') or len(parts) == 1

    if is_list_request:
        if not is_safe_path(path, team):
            return
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
                    _print_ramble(file_to_read, sops_file_override, Path(selected_file_name).stem, team)
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
        _print_ramble(full_path, sops_file_override, target, team)

def handleCreateRamble(args):
    ramble = args.target
    team = getattr(args, 'team', None)
    CONFIG_DIR = _get_ramble_dir(team)

    if '.' in ramble:
        parts = ramble.split('.', 1)
        directory = parts[0]
        page = parts[1]
        if not page or ".." in directory or "/" in directory:
            console.print(f"[bold red]ERROR:[/] Invalid format for journal.page")
            sys.exit(1)
        path = CONFIG_DIR / directory
        CONFIG_FILE_PATH = path / f'{page}.yml'

        if not is_safe_path(CONFIG_FILE_PATH, team):
            sys.exit(1)

        baseText=f"""title: {page}
concept:
what:
why:
how:
scripts:
"""
        if not path.exists():
            path.mkdir(parents=True, exist_ok=True)
            console.print(f'[yellow]Created new journal: {directory}![/]')

        try:
            with open(CONFIG_FILE_PATH, 'x') as f:
                f.write(baseText)
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
        if ".." in ramble or "/" in ramble:
            console.print(f"[bold red]ERROR:[/] Invalid format for journal")
            sys.exit(1)

        path = CONFIG_DIR / ramble
        fullPath = path / f'{ramble}.yml'

        if not is_safe_path(fullPath, team):
            sys.exit(1)

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
                with open(fullPath, 'x') as f:
                    f.write(baseText)
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
    if ".." in ramble or "/" in ramble:
        console.print(f"[bold red]ERROR:[/] Invalid format for ramble.")
        sys.exit(1)

    team = getattr(args, 'team', None)
    CONFIG_DIR = _get_ramble_dir(team)

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
        if not is_safe_path(file_path, team):
            sys.exit(1)

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
        CONFIG_FILE_PATH = path / f'{page}.yml'

        if not CONFIG_FILE_PATH.exists():
            if not is_safe_path(path, team):
                 sys.exit(1)
            console.print(f'[bold red]ERROR:[/] Ramble page not found: {CONFIG_FILE_PATH}')
            sys.exit(1)

        edit_file(CONFIG_FILE_PATH)
        sys.exit(0)

    path = CONFIG_DIR / ramble
    if not is_safe_path(path, team):
        sys.exit(1)

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
    if ".." in ramble or "/" in ramble:
        console.print(f"[bold red]ERROR:[/] Invalid format for ramble.")
        sys.exit(1)

    keys = args.keys or []
    team = getattr(args, 'team', None)
    CONFIG_DIR = _get_ramble_dir(team)

    if not '.' in ramble:
        console.print('[bold red]ERROR:[/] You must pass a specific page to be encrypted (e.g., diary.page).')
        sys.exit(1)

    parts = ramble.split('.', 1)
    directory = parts[0]
    page = parts[1]

    path = CONFIG_DIR / directory
    fullPath = path / f'{page}.yml'

    if not is_safe_path(fullPath, team):
        sys.exit(1)

    if not fullPath.exists():
        console.print(f"[bold red]ERROR:[/] Ramble page not found: {fullPath}")
        sys.exit(1)

    try:
        data = OmegaConf.load(fullPath)
    except Exception as e:
        console.print(f'[bold red]ERROR:[/] Could not read ramble file: {e}')
        sys.exit(1)

    keysInData = data.keys()
    baseKeys = ['title', 'concept', 'sops', 'tags']

    if not keys:
        keys = [str(key) for key in keysInData if key not in baseKeys and key != 'tags']

    if not keys:
        console.print('[yellow]No new keys to encrypt. Exiting.[/]')
        sys.exit(0)

    joinKeys = '|'.join(keys)
    regex = f"^({joinKeys})$"
    console.print(f'[italic][yellow]Encrypting these keys:[/][cyan] {keys}[/][/]')

    if 'sops' in data:
        try:
            result = subprocess.run(['sops', '--config', sops_file_override, '-d', str(fullPath)], capture_output=True, text=True, check=True)
            with tempfile.NamedTemporaryFile(mode='w', delete=False, dir=fullPath.parent, suffix=".yml") as tmp:
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

    team = getattr(args, 'team', None)

    for target in args.targets:
        _process_ramble_target(target, sops_file_override, team)

    sys.exit(0)

def handleFindRamble(args):
    from rich.table import Table
    from rich.panel import Panel
    from rich.align import Align
    from itertools import zip_longest

    team = getattr(args, 'team', None)
    RAMBLE_DIR = _get_ramble_dir(team)
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

    if search_term:
        for ramble_file in RAMBLE_DIR.rglob("*.yml"):
            data, text = _read_ramble_content(ramble_file, sops_file_override, team)

            if data is None or text is None:
                continue

            if required_tag:
                tags = data.get('tags', [])
                if required_tag not in tags:
                    continue

            if search_term.lower() not in text.lower():
                continue
            ramble = ramble_file.parent.name
            page = ramble_file.stem
            results.append(f"{ramble}.{page}")
    elif required_tag:
        for ramble_file in RAMBLE_DIR.rglob("*.yml"):
            data, _ = _read_ramble_content(ramble_file, sops_file_override, team)
            if data is None:
                continue

            tags = data.get('tags', [])
            if required_tag in tags:
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
    team = getattr(args, 'team', None)
    RAMBLE_DIR = _get_ramble_dir(team)
    old = args.old
    new = args.new

    if ".." in old or "/" in old or ".." in new or "/" in new:
        console.print(f"[bold red]ERROR:[/] Invalid format for ramble.")
        sys.exit(1)

    old_is_dir = '.' not in old
    new_is_dir = '.' not in new

    if old_is_dir:
        source_path = RAMBLE_DIR / old
    else:
        try:
            old_journal, old_page = old.split('.', 1)
            source_path = RAMBLE_DIR / old_journal / f"{old_page}.yml"
        except ValueError:
            console.print(f"[bold red]ERROR:[/] Invalid source format: '{old}'")
            sys.exit(1)

    if not is_safe_path(source_path, team):
        sys.exit(1)

    dest_file_path = None
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

    if not is_safe_path(dest_dir_path, team):
        sys.exit(1)
    if dest_file_path and not is_safe_path(dest_file_path, team):
        sys.exit(1)

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

    if not old_is_dir and not new_is_dir and dest_file_path:
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

    if old_is_dir and not new_is_dir:
        console.print("[bold red]ERROR:[/] system cannot move a directory to a singular file")
        sys.exit(1)

    if not old_is_dir and new_is_dir:
        if not source_path.is_file():
            console.print(f"[bold red]ERROR:[/] No such page (file): {source_path}")
            sys.exit(1)

        final_dest_file = dest_dir_path / source_path.name

        if not is_safe_path(final_dest_file, team):
            sys.exit(1)

        if final_dest_file.exists():
            console.print(f"[bold red]ERROR:[/] Page (file) '{source_path.name}' already exists in journal '{new}'")
            sys.exit(1)

        dest_dir_path.mkdir(parents=True, exist_ok=True)
        shutil.move(str(source_path), str(final_dest_file))
        new_ramble_name = f"{new}.{source_path.stem}"
        console.print(f"[green]Successfully moved page '{old}' to '{new_ramble_name}'[/]")
        sys.exit(0)

def handleDelRamble(args):
    team = getattr(args, 'team', None)
    RAMBLE_DIR = _get_ramble_dir(team)
    ramble = args.ramble

    if ".." in ramble or "/" in ramble:
        console.print(f"[bold red]ERROR:[/] Invalid format for ramble.")
        sys.exit(1)

    if '.' in ramble:
        parts = ramble.split('.', 1)
        journal = parts[0]
        page = parts[1]
        rambleFile = RAMBLE_DIR / journal / f"{page}.yml"

        if not is_safe_path(rambleFile, team):
            sys.exit(1)

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

        if not is_safe_path(ramblePath, team):
            sys.exit(1)

        if not ramblePath.exists():
            console.print(f"[bold red]ERROR:[/] {ramblePath} does not exist.")
            sys.exit(1)

        confirmation = Confirm.ask(f"Are you [red][italic]sure[/][/] you want to delete the entire journal '{ramble}'?", default=False)
        if confirmation:
            console.print(f"[bold red]Removing {ramble}.[/]")
            shutil.rmtree(ramblePath)
            sys.exit(0)
        console.print("[green]Alright![/] Aborting.")

def handleUpdateEncryptRamble(args):
    team = getattr(args, 'team', None)
    RAMBLE_DIR = _get_ramble_dir(team)
    GLOBAL_CONFIG_DIR = os.path.expanduser("~/.config/chaos")
    GLOBAL_CONFIG_FILE_PATH = os.path.join(GLOBAL_CONFIG_DIR, "config.yml")
    global_config = {}
    updated_count = 0

    if os.path.exists(GLOBAL_CONFIG_FILE_PATH):
        global_config = OmegaConf.load(GLOBAL_CONFIG_FILE_PATH) or OmegaConf.create()

    sops_file_override = None
    if hasattr(args, 'sops_file_override') and args.sops_file_override:
        sops_file_override = args.sops_file_override
    else:
        sops_file_override = global_config.get('sops_file')

    for ramble_file in RAMBLE_DIR.rglob("*.yml"):
        if not is_safe_path(ramble_file, team):
            continue
        try:
            data = OmegaConf.load(ramble_file)
            if "sops" in data:
                if not sops_file_override:
                    console.print('[bold red]ERROR:[/] An encrypted ramble was found, but no sops configuration was provided.')
                    console.print("   Provide one with '[cyan]-ss /path/to/.sops.yml[/cyan]' or set a default with '[cyan]chaos set sops /path/to/.sops.yml[/cyan]'.")
                    sys.exit(1)

                console.print(f"Checking for key updates in [cyan]{ramble_file.relative_to(RAMBLE_DIR)}[/]...")
                result = subprocess.run(
                    ['sops', '--config', sops_file_override, 'updatekeys', str(ramble_file)],
                    capture_output=True, text=True, check=True, input="y"
                )
                updated_count += 1
        except subprocess.CalledProcessError as e:
            console.print(f'[bold red]ERROR: Ramble key update with sops failed for {ramble_file}.[/]\n{e.stderr}')
            sys.exit(1)
        except FileNotFoundError:
            console.print(f"[bold red]ERROR:[/] `sops` command not found. Please ensure sops is installed and in your PATH.")
            sys.exit(1)
        except Exception as e:
            console.print(f'[bold yellow]Warning:[/] Could not read or parse ramble file: {ramble_file}. Skipping.')
            continue

    if updated_count > 0:
        console.print(f"\n[bold green]Processed {updated_count} encrypted ramble(s).[/]")
    else:
        console.print("[yellow]No encrypted ramble files found to update.[/]")

    sys.exit(0)
