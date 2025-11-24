#!/usr/bin/env python3
import logging
import argparse
import getpass
import os
import sys
import subprocess
import argcomplete
import json
import site
import glob

from importlib import import_module
from argcomplete.completers import FilesCompleter

from rich.console import Console, Group
from rich.panel import Panel
from rich.markdown import Markdown
from rich.syntax import Syntax
from rich.tree import Tree
from rich.text import Text
import io

from omegaconf import OmegaConf
from pathlib import Path

from pyinfra.api.inventory import Inventory
from pyinfra.api.config import Config
from pyinfra.api.connect import connect_all, disconnect_all
from pyinfra.api.state import StateStage, State
from pyinfra.api.operations import run_ops
from pyinfra.context import ctx_state

from importlib.metadata import entry_points

pluginDevPath = os.getenv('CHAOS_DEV_PATH', None)
if pluginDevPath:
    absPath = os.path.abspath(pluginDevPath)
    if os.path.exists(absPath):
        sys.path.insert(0, pluginDevPath)
    else:
        print(f"Warning: Ch-aos plugin path '{absPath}' does not exist.", file=sys.stderr)

def get_plugins(update_cache=False):
    plugin_dirs = [
        Path.home() / ".local/share/chaos/plugins",
        Path("/usr/share/chaos/plugins")
    ]

    for plugin_dir in plugin_dirs:
        if not plugin_dir.exists():
            continue

        wheel_files = list(plugin_dir.glob("*.whl"))
        for whl in wheel_files:
            try:
                whl_path = str(whl.resolve())

                if whl_path not in sys.path:
                    sys.path.insert(0, whl_path) 

            except Exception as e:
                print(f"Warning: Could not load plugin wheel '{whl}': {e}", file=sys.stderr)

    CACHE_DIR = Path(os.path.expanduser("~/.cache/chaos"))
    CACHE_FILE = CACHE_DIR / "plugins.json"
    cache_exists = CACHE_FILE.exists()

    if not update_cache and cache_exists:
        with open(CACHE_FILE, 'r') as f:
            try:
                cache_data = json.load(f)
                if 'roles' in cache_data and 'aliases' in cache_data and 'explainations' in cache_data:
                    return cache_data['roles'], cache_data['aliases'], cache_data['explainations']
                else:
                    print("Warning: Invalid or outdated cache file format. Re-discovering plugins.", file=sys.stderr)
            except json.JSONDecodeError:
                print("Warning: Could not read cache file. Re-discovering plugins.", file=sys.stderr)

    discovered_roles = {}
    discovered_aliases = {}
    discovered_explainations = {}
    eps = entry_points()

    role_eps = eps.select(group="chaos.roles") if hasattr(eps, "select") else eps.get("chaos.roles", [])
    for ep in role_eps:
        discovered_roles[ep.name] = ep.value

    alias_eps = eps.select(group="chaos.aliases") if hasattr(eps, "select") else eps.get("chaos.aliases", [])
    for ep in alias_eps:
        discovered_aliases[ep.name] = ep.value

    exp_eps = eps.select(group="chaos.explain") if hasattr(eps, "select") else eps.get("chaos.explain", [])
    for ep in exp_eps:
        discovered_explainations[ep.name] = ep.value

    try:
        CACHE_DIR.mkdir(parents=True, exist_ok=True)
        with open(CACHE_FILE, 'w') as f:
            json.dump({'roles': discovered_roles, 'aliases': discovered_aliases, 'explainations': discovered_explainations}, f, indent=4)
        if update_cache or not cache_exists:
            print(f"Plugin cache saved to {CACHE_FILE}", file=sys.stderr)
    except OSError as e:
        print(f"Error: Could not write to cache file {CACHE_FILE}: {e}", file=sys.stderr)


    return discovered_roles, discovered_aliases, discovered_explainations

def load_roles(roles_spec):
    loaded_roles = {}
    for name, spec in roles_spec.items():
        try:
            module_name, func_name = spec.split(':', 1)
            module = import_module(module_name)
            loaded_roles[name] = getattr(module, func_name)
        except (ImportError, AttributeError, ValueError) as e:
            print(f"Warning: Could not load role '{name}' from spec '{spec}': {e}", file=sys.stderr)
    return loaded_roles

class RolesCompleter:
    def __init__(self):
        self._roles = None
        self._aliases = None
        self.explain = None

    def __call__(self, prefix, **kwargs):
        if self._roles is None or self._aliases is None or self.explain is None:
            self. _roles, self._aliases, self.explain = get_plugins()

        all_comps = list(self._roles.keys()) + list(self._aliases.keys()) + list(self.explain.keys())
        return [comp for comp in all_comps if comp.startswith(prefix)]

def argParsing():
    parser = argparse.ArgumentParser(
        description="chaos system manager.",
        epilog="Use 'chaos <tags...>' to run roles, or 'chaos explain <topic>' for details."
    )

    parser.add_argument('-e', dest="chobolo", help="Path to Ch-obolo to be used (overrides all calls).").completer = FilesCompleter()
    parser.add_argument('-u', '--update-plugins', action='store_true', help="Force update of the plugin cache.")
    parser.add_argument('-r', '--roles', action='store_true', help="Check which roles are available.")
    parser.add_argument('-a', '--aliases', action='store_true', help="Check which aliases are available.")
    parser.add_argument('-ikwid', '-y', '--i-know-what-im-doing', action='store_true', help="Skips all confirmations for role execution.")
    parser.add_argument('--dry', '-d', action='store_true', help="Execute roles in dry mode.")
    parser.add_argument('-v', action='count', default=0, help="Increase verbosity level.")
    parser.add_argument('--verbose', type=int, choices=[1, 2, 3], help="Set log level directly.")
    parser.add_argument('--secrets-file', '-sf', dest='secrets_file_override', help="Path to the sops-encrypted secrets file (overrides all calls).").completer = FilesCompleter()
    parser.add_argument('--sops-file', '-ss', dest='sops_file_override', help="Path to the .sops.yaml config file (overrides all calls).").completer = FilesCompleter()
    parser.add_argument('--set-chobolo', '-chobolo', dest='set_chobolo_file', help="Set and save the default Ch-obolo file path.").completer = FilesCompleter()
    parser.add_argument('--set-sec-file', '-sec', dest='set_secrets_file', help="Set and save the default secrets file path.").completer = FilesCompleter()
    parser.add_argument('--set-sops-file', '-sops', dest='set_sops_file', help="Set and save the default sops config file path.").completer = FilesCompleter()
    parser.add_argument('--check-sec', '-cs', action='store_true', help="Check the secrets encrypted file. Do not run publicly.")
    parser.add_argument('--edit-sec', '-es', action='store_true', help="Edit the secrets encrypted file using sops. Do not run publicly.")
    parser.add_argument('-ec', '--edit-chobolo', action='store_true', help="Edit the Ch-obolo file using the default editor.")
    parser.add_argument('-gt', '--generate-tab', action='store_true', help="Generate shell tab-completion script.")
    parser.add_argument('-ex', '--explain', nargs='+', help="Explain a role or topic (e.g., 'users', 'users.sudo').")
    parser.add_argument('-le', '--list-explainations', action='store_true', help="List all available explanation topics.")
    parser.add_argument('--details', choices=['basic', 'intermediate', 'advanced'], default='basic', help="Level of detail for the explanation.")
    tags = parser.add_argument('tags', nargs='*', help="The tag(s) for the role(s) to be executed.")
    tags.completer = RolesCompleter()

    return parser

def checkRoles(ROLES_DISPATCHER):
    print("Discovered Roles:")
    if not ROLES_DISPATCHER:
        print("No roles found.")
    else:
        for p in ROLES_DISPATCHER:
            print(f"  -{p}")
    sys.exit(0)

def checkExplainations(EXPLAINATIONS):
    print("Discovered Explainations:")
    if not EXPLAINATIONS:
        print("No explainations found.")
    else:
        for p in EXPLAINATIONS:
            print(f"  -{p}")
    sys.exit(0)


def checkAliases(ROLE_ALIASES):
    print("Discovered Aliases for Roles:")
    if not ROLE_ALIASES:
        print("No aliases found.")
    else:
        for p, r in ROLE_ALIASES.items():
            print(f"\n  -{p} ~> -{r}")
            print("_____________________________________________")
    sys.exit(0)

def setMode(args):
    CONFIG_DIR = os.path.expanduser("~/.config/chaos")
    CONFIG_FILE_PATH = os.path.join(CONFIG_DIR, "config.yml")

    print(f"Saving configuration to {CONFIG_FILE_PATH}...")

    os.makedirs(CONFIG_DIR, exist_ok=True)

    if os.path.exists(CONFIG_FILE_PATH):
        global_config = OmegaConf.load(CONFIG_FILE_PATH)
    else:
        global_config = OmegaConf.create()

    if args.set_chobolo_file:
        inputPath = Path(args.set_chobolo_file)
        try:
            absolutePath = inputPath.resolve(strict=True)
            global_config.chobolo_file = str(absolutePath)
            print(f"- Default Ch-obolo set to: {args.set_chobolo_file}")
        except FileNotFoundError:
            print(f"ERRO: Arquivo não encontrado em: {inputPath}", file=sys.stderr)
            sys.exit(1)
    if args.set_secrets_file:
        inputPath = Path(args.set_secrets_file)
        try:
            absolutePath = inputPath.resolve(strict=True)
            global_config.secrets_file = str(absolutePath)
            print(f"- Default secrets file set to: {args.set_secrets_file}")
        except FileNotFoundError:
            print(f"ERRO: Arquivo não encontrado em: {inputPath}", file=sys.stderr)
            sys.exit(1)
    if args.set_sops_file:
        inputPath = Path(args.set_sops_file)
        try:
            absolutePath = inputPath.resolve(strict=True)
            global_config.sops_file = str(absolutePath)
            print(f"- Default sops file set to: {args.set_sops_file}")
        except FileNotFoundError:
            print(f"ERRO: Arquivo não encontrado em: {inputPath}", file=sys.stderr)
            sys.exit(1)

    OmegaConf.save(global_config, CONFIG_FILE_PATH)
    print("Configuration saved.")

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
    console = Console() # Initialize console

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
        console.print("[bold red]ERROR:[/] No Ch-obolo passed", file=sys.stderr)
        console.print("   Use '[cyan]-e /path/to/file.yml[/cyan]' or configure a base Ch-obolo with '[cyan]chaos --set-chobolo /path/to/file.yml[/cyan]'.", file=sys.stderr)
        sys.exit(1)

    # -----------------------------
    # ---- Pyinfra Setup ----

    hosts = ["@local"]
    inventory = Inventory((hosts, {}))
    config = Config()
    state = State(inventory, config)
    state.current_stage = StateStage.Prepare
    ctx_state.set(state)

    console.print("[bold magenta]Sudo password:[/bold magenta] ")
    config.SUDO_PASSWORD = getpass.getpass()

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
                    console.print(f"\n[bold yellow]WARNING:[/] Could not determine a mode for tag '{tag}'. Skipping.", file=sys.stderr)
            else:
                ROLES_DISPATCHER[normalized_tag](*commonArgs)

            console.print(f"\n--- '[bold blue]{normalized_tag}[/bold blue]' role finalized. ---\n")
        else:
            console.print(f"\n[bold yellow]WARNING:[/] Unknown tag '{normalized_tag}'. Skipping.", file=sys.stderr)

    if not dry:
        run_ops(state)
    else:
        console.print("[bold yellow]dry mode active, skipping.[/bold yellow]")

    # --- Disconnection ---
    console.print("\nDisconnecting...")
    disconnect_all(state)
    console.print("[bold green]Finalized.[/bold green]")

def runSopsCheck(sops_file_override, secrets_file_override):
    secretsFile = secrets_file_override
    sopsFile = sops_file_override

    CONFIG_DIR = os.path.expanduser("~/.config/chaos")
    CONFIG_FILE_PATH = os.path.join(CONFIG_DIR, "config.yml")

    global_config = {}
    if os.path.exists(CONFIG_FILE_PATH):
        global_config = OmegaConf.load(CONFIG_FILE_PATH) or OmegaConf.create()

    if not secretsFile:
        secretsFile = global_config.get('secrets_file')
    if not sopsFile:
        sopsFile = global_config.get('sops_file')

    if not secretsFile or not sopsFile:
        ChOboloPath = global_config.get('chobolo_file', None)
        if ChOboloPath:
            try:
                ChObolo = OmegaConf.load(ChOboloPath)
                secrets_config = ChObolo.get('secrets', None)
                if secrets_config:
                    if not secretsFile:
                        secretsFile = secrets_config.get('sec_file')
                    if not sopsFile:
                        sopsFile = secrets_config.get('sec_sops')
            except Exception as e:
                print(f"WARNING: Could not load Chobolo fallback '{ChOboloPath}': {e}", file=sys.stderr)

    if not secretsFile or not sopsFile:
        print("ERROR: SOPS check requires both secrets file and sops config file paths.", file=sys.stderr)
        print("       Configure them using 'chaos -sec' and 'chaos -sops', or pass them with '-sf' and '-ss'.", file=sys.stderr)
        sys.exit(1)

    try:
        result = subprocess.run(['sops', '--config', sopsFile, '--decrypt', secretsFile], check=True)
        okCodes= [0,200]
        if result.returncode not in okCodes:
            raise subprocess.CalledProcessError(result.returncode, result.args, result.stdout, result.stderr)
    except subprocess.CalledProcessError as e:
        print("ERROR: SOPS decryption failed.")
        print("Details:", e.stderr)
        sys.exit(1)
    except FileNotFoundError:
        print("ERROR: 'sops' command not found. Please ensure sops is installed and in your PATH.", file=sys.stderr)
        sys.exit(1)

def runSopsEdit(sops_file_override, secrets_file_override):
    secretsFile = secrets_file_override
    sopsFile = sops_file_override

    CONFIG_DIR = os.path.expanduser("~/.config/chaos")
    CONFIG_FILE_PATH = os.path.join(CONFIG_DIR, "config.yml")

    global_config = {}
    if os.path.exists(CONFIG_FILE_PATH):
        global_config = OmegaConf.load(CONFIG_FILE_PATH) or OmegaConf.create()

    if not secretsFile:
        secretsFile = global_config.get('secrets_file')
    if not sopsFile:
        sopsFile = global_config.get('sops_file')

    if not secretsFile or not sopsFile:
        ChOboloPath = global_config.get('chobolo_file', None)
        if ChOboloPath:
            try:
                ChObolo = OmegaConf.load(ChOboloPath)
                secrets_config = ChObolo.get('secrets', None)
                if secrets_config:
                    if not secretsFile:
                        secretsFile = secrets_config.get('sec_file')
                    if not sopsFile:
                        sopsFile = secrets_config.get('sec_sops')
            except Exception as e:
                print(f"WARNING: Could not load Chobolo fallback '{ChOboloPath}': {e}", file=sys.stderr)

    if not secretsFile or not sopsFile:
        print("ERROR: SOPS check requires both secrets file and sops config file paths.", file=sys.stderr)
        print("       Configure them using 'chaos -sec' and 'chaos -sops', or pass them with '-sf' and '-ss'.", file=sys.stderr)
        sys.exit(1)

    try:
        result = subprocess.run(['sops', '--config', sopsFile, secretsFile], check=True)
        okCodes= [0,200]
        if result.returncode not in okCodes:
            raise subprocess.CalledProcessError(result.returncode, result.args, result.stdout, result.stderr)
    except subprocess.CalledProcessError as e:
        sys.exit(0)
    except FileNotFoundError:
        print("ERROR: 'sops' command not found. Please ensure sops is installed and in your PATH.", file=sys.stderr)
        sys.exit(1)

def runChoboloEdit(chobolo_path):
    editor = os.getenv('EDITOR', 'nano')
    if not chobolo_path:
        CONFIG_DIR = os.path.expanduser("~/.config/chaos")
        CONFIG_FILE_PATH = os.path.join(CONFIG_DIR, "config.yml")
        cfg = OmegaConf.load(CONFIG_FILE_PATH)
        chobolo_path = cfg.get('chobolo_file', None)
    if chobolo_path:
        try:
            result = subprocess.run(
                [editor, chobolo_path],
            )
        except subprocess.CalledProcessError as e:
            print("ERROR: Ch-obolo editing failed.")
            print("Details: Editor exited with error code", e.returncode)
            sys.exit(1)
        except FileNotFoundError:
            print(f"ERROR: Editor '{editor}' not found. Please ensure it is installed and in your PATH.", file=sys.stderr)
            sys.exit(1)
    else:
        print("ERROR: No Ch-obolo file configured to edit.", file=sys.stderr)
        sys.exit(1)

def handleGenerateTab():
    subprocess.run(['register-python-argcomplete', 'chaos'])

def handleExplain(args, EXPLAIN_DISPATCHER):
    console = Console()
    DETAIL_LEVELS = {
        'basic': ['what', 'why', 'examples'],
        'intermediate': ['what', 'why', 'how', 'commands', 'equivalent', 'examples'],
        'advanced': ['concept', 'what', 'why', 'how', 'commands', 'files', 'security', 'equivalent', 'examples', 'validation', 'learn_more']
    }

    topics = args.explain
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

            if hasattr(explainObj, methodName):
                method = getattr(explainObj, methodName)
                explanation = method()

                explanation_renderables = []

                if 'what' in keysToShow and explanation.get('what'):
                    explanation_renderables.append(Markdown(f"**What is it:** {explanation['what']}"))
                    explanation_renderables.append(Text("\n"))

                if 'why' in keysToShow and explanation.get('why'):
                    explanation_renderables.append(Markdown(f"**Why use it:** {explanation['why']}"))
                    explanation_renderables.append(Text("\n"))

                commands = explanation.get('commands', [])
                if 'equivalent' in keysToShow and commands:
                    tree = Tree("[bold]Equivalent command (Linux)[/]")
                    for command in commands:
                        tree.add(f"[cyan]{command}[/cyan]")
                    explanation_renderables.append(tree)
                    explanation_renderables.append(Text("\n"))

                files = explanation.get('files', [])
                if 'files' in keysToShow and files:
                    tree = Tree("[bold]Relevant files[/]")
                    for f in files:
                        tree.add(f"[green]{f}[/green]")
                    explanation_renderables.append(tree)
                    explanation_renderables.append(Text("\n"))

                examples = explanation.get('examples', [])
                if 'examples' in keysToShow and examples:
                    explanation_renderables.append(Markdown("**Examples:**"))
                    for ex in examples:
                        if 'yaml' in ex:
                            explanation_renderables.append(Syntax(ex['yaml'], "yaml", theme="monokai", line_numbers=True))
                        if 'equivalent' in ex:
                             explanation_renderables.append(Text.from_markup(f"[italic]This is equivalent to:[/] [cyan]{ex['equivalent']}[/cyan]"))
                    explanation_renderables.append(Text("\n"))



                if 'how' in keysToShow and explanation.get('how'):
                    explanation_renderables.append(Markdown(f"**How it works:** {explanation['how']}"))
                    explanation_renderables.append(Text("\n"))

                if 'validation' in keysToShow and explanation.get('validation'):
                     explanation_renderables.append(Markdown(f"**Validation:** {explanation['validation']}"))
                     explanation_renderables.append(Text("\n"))

                learn_more = explanation.get('learn_more', [])
                if 'learn_more' in keysToShow and learn_more:
                    tree = Tree("[bold]Learn more[/]")
                    for item in learn_more:
                        tree.add(f"[blue]{item}[/blue]")
                    explanation_renderables.append(tree)
                    explanation_renderables.append(Text("\n"))

                if 'security' in keysToShow and explanation.get('security'):
                    explanation_renderables.append(Panel(explanation['security'], title="[bold yellow]Security considerations[/]", border_style="yellow", expand=False))
                    explanation_renderables.append(Text("\n"))

                console.print(
                    Panel(
                        Group(*explanation_renderables),
                        title=f"[bold green]Explanation for topic '{topic}'[/] ([italic]{args.details}[/])",
                        border_style="green",
                        expand=True,
                        width=80 if len(explanation_renderables) > 1 else None,
                    )
                )

            else:
                available_methods = [m.replace('explain_', '') for m in dir(explainObj) if m.startswith('explain_') and m != 'explain_']
                console.print(f"[bold red]ERROR:[/] No explanation found for sub-topic '{sub_topic}' in role '{role}'.")
                if available_methods:
                    console.print(f"Available sub-topics for '{role}': [yellow]{available_methods}[/yellow]")
        else:
            console.print(f"[bold red]ERROR:[/] No explanation found for topic '{topic}'.")

def main():
    try:
        parser = argParsing()

        argcomplete.autocomplete(parser)

        args = parser.parse_args()

        if args:
            role_specs, ROLE_ALIASES, EXPLAINATIONS = get_plugins(args.update_plugins)

            if args.list_explainations:
                checkExplainations(EXPLAINATIONS)
                sys.exit(0)
            
            if args.explain:
                handleExplain(args, EXPLAINATIONS)
                sys.exit(0)

            if args.verbose or args.v > 0:
                handleVerbose(args)

            if args.generate_tab:
                handleGenerateTab()
                sys.exit(0)

            if args.check_sec:
                runSopsCheck(args.sops_file_override, args.secrets_file_override)
                sys.exit(0)

            if args.edit_sec:
                runSopsEdit(args.sops_file_override, args.secrets_file_override)
                sys.exit(0)

            if args.edit_chobolo:
                runChoboloEdit(args.chobolo)
                sys.exit(0)

            if args.aliases:
                checkAliases(ROLE_ALIASES)

            if args.roles:
                checkRoles(role_specs)

            is_setter_mode = any([args.set_chobolo_file, args.set_secrets_file, args.set_sops_file])
            if is_setter_mode:
                setMode(args)
                sys.exit(0)

            if not args.tags:
                print('No tags passed.')
                sys.exit(0)

            ROLES_DISPATCHER = load_roles(role_specs)
            ikwid = args.i_know_what_im_doing
            dry = args.dry
            handleOrchestration(args, dry, ikwid, ROLES_DISPATCHER, ROLE_ALIASES)
        else:
            print("No arguments passed.")
            parser.parse_args(['-h'])
    except KeyboardInterrupt:
        print("\nOperation cancelled by user.", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
  main()
