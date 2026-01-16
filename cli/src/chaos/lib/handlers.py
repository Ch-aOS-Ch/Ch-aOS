import sys
from typing import cast
from rich.console import Console
from rich.prompt import Confirm
from pathlib import Path
from omegaconf import DictConfig, OmegaConf
import logging
import os
import getpass

console = Console()

"""
Orchestration/Explanation Handlers for Chaos CLI

I KNOW IT'S MESSY, IT'S INTENTIONAL.
Big function = easier to read flow, more explicit and less jumping around files.
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
def _get_configs(args):
    CONFIG_DIR = os.path.expanduser("~/.config/chaos")
    CONFIG_FILE_PATH = os.path.join(CONFIG_DIR, "config.yml")
    global_config = OmegaConf.create()
    if os.path.exists(CONFIG_FILE_PATH):
        global_config = OmegaConf.load(CONFIG_FILE_PATH) or OmegaConf.create()
        global_config = cast(DictConfig, global_config)

    chobolo_path = args.chobolo or global_config.get('chobolo_file', None)
    secrets_file_override = args.secrets_file_override or global_config.get('secrets_file', None)
    sops_file_override = args.sops_file_override or global_config.get('sops_file', None)

    if not chobolo_path:
        raise FileNotFoundError("No Ch-obolo passed\n"
                            "   Use '[cyan]-e /path/to/file.yml[/cyan]' or configure a base Ch-obolo with '[cyan]chaos set chobolo /path/to/file.yml[/cyan]'.")

    return global_config, chobolo_path, secrets_file_override, sops_file_override

def _handle_fleet(args, chobolo_config, chobolo_path, ikwid):
    isFleet = False
    if hasattr(args, 'fleet') and args.fleet:
        chobolo_config = cast(DictConfig, chobolo_config)
        fleet_config = chobolo_config.get('fleet')

        if fleet_config:
            parallels = fleet_config.get('parallelism', 0)
            fleet_hosts = fleet_config.get('hosts', [])

            if fleet_hosts:
                hosts = []
                container = OmegaConf.to_container(fleet_hosts, resolve=True)

                if not isinstance(container, list):
                    raise ValueError(f"Fleet hosts configuration in {chobolo_path} is malformed. Expected a list of dicts of hosts.")

                for host_item in container:
                    if not isinstance(host_item, dict) or len(host_item) != 1:
                        console.print(f"[bold yellow]WARNING:[/] Malformed host entry in fleet configuration: {host_item}. It must be a dictionary with a single host name as the key. Skipping.")
                        continue

                    hostname = list(host_item.keys())[0]
                    host_data = host_item[hostname]
                    if not isinstance(host_data, dict):
                        console.print(f"[bold yellow]WARNING:[/] Malformed host data for host '{hostname}' in fleet configuration. It must be a dictionary of host parameters. Skipping.")
                        continue

                    hosts.append((hostname, host_data))
                isFleet = True

                if not hosts:
                    console.print(f"[bold yellow]WARNING:[/] No valid fleet hosts found in chobolo file in {chobolo_path}, defaulting to localhost.")
                    hosts = ["@local"]
                    isFleet = False
                    parallels = 0
                    
                return isFleet, parallels, hosts
            else:
                confirm = False if ikwid else Confirm.ask(f'[bold yellow]WARNING:[/] No fleet hosts configured for chobolo file in {chobolo_path}, do you wish to continue? (will use localhost)', default=False)
                if not confirm:
                    console.print('Exiting...')
                    sys.exit(0)
                return False, 0, ["@local"]
        else:
            confirm = False if ikwid else Confirm.ask(f'[bold yellow]WARNING:[/] No fleet configuration found in chobolo file {chobolo_path}, do you wish to continue? (will use localhost)', default=False)
            if not confirm:
                console.print('Exiting...')
                sys.exit(0)
            return False, 0, ["@local"]
    return False, 0, ["@local"]

def setup_fleet_hosts(args, chobolo_config, chobolo_path, ikwid):
    from pyinfra.api.inventory import Inventory
    parallels = 0
    hosts = ["@local"]

    isFleet, parallels, hosts = _handle_fleet(args, chobolo_config, chobolo_path, ikwid)

    if not isFleet:
        inventory = Inventory((hosts, {}))
    else:
        inventory = Inventory(hosts)

    return inventory, hosts, parallels

def _setup_pyinfra_connection(args, chobolo_config, chobolo_path, ikwid):
    # --- Lazy import pyinfra components ---
    from pyinfra.api.config import Config
    from pyinfra.api.connect import connect_all
    from pyinfra.api.state import StateStage, State
    from pyinfra.context import ctx_state
    # ------------------------------------

    inventory, hosts, parallels = setup_fleet_hosts(args, chobolo_config, chobolo_path, ikwid)

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

    return state, skip

def _setup_user_aliases(console: Console, userAliases: DictConfig, ROLE_ALIASES: DictConfig):
    for a in userAliases.keys():
        if a in ROLE_ALIASES:
            console.print(f"[bold yellow]WARNING:[/] Alias {a} already exists in Aliases installed. Skipping.")
            del userAliases[a]
    return userAliases

def _setup_normalized_tag(tag: str, ROLE_ALIASES: DictConfig):
    if ROLE_ALIASES:
        normalized_tag = ROLE_ALIASES.get(tag, tag)
    else:
        normalized_tag = tag
    return normalized_tag

def handleSecRoles(normalized_tag, enabledSecPlugins, skip, decrypted_secrets, commonArgs, ROLES_DISPATCHER: DictConfig, secrets_file_override, sops_file_override, global_config, args):
    if normalized_tag in enabledSecPlugins:
        confirm = True if skip else Confirm.ask(f"You are about to use a external plugin as Secret having plugin:\n[bold yellow]{normalized_tag}[/]\nAre you sure you want to continue?", default=False)
        if not confirm:
            return

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
                return

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

def _run_tags(
    ROLES_DISPATCHER,
    ROLE_ALIASES: DictConfig,
    SEC_HAVING_ROLES: set,
    skip: bool,
    decrypted_secrets: tuple,
    commonArgs: tuple,
    secrets_file_override,
    sops_file_override,
    global_config,
    args,
    console_err,
    host,
):
            for tag in args.tags:
                normalized_tag = _setup_normalized_tag(tag, ROLE_ALIASES)
                if normalized_tag in ROLES_DISPATCHER:
                    if normalized_tag in SEC_HAVING_ROLES:
                        handleSecRoles(
                            normalized_tag,
                            SEC_HAVING_ROLES,
                            skip,
                            decrypted_secrets,
                            commonArgs,
                            ROLES_DISPATCHER,
                            secrets_file_override,
                            sops_file_override,
                            global_config,
                            args
                        )

                    elif normalized_tag == 'packages':
                        mode = ''
                        if tag in ['allPkgs', 'packages', 'pkgs']:
                            mode = 'all'
                        elif tag == 'natPkgs':
                            mode = 'native'
                        elif tag == 'aurPkgs':
                            mode = 'aur'

                        if not mode:
                            console_err.print(f"\n[bold yellow]WARNING:[/] Could not determine a mode for tag '{tag}'. Skipping.")

                        pkgArgs = commonArgs + (mode,)
                        ROLES_DISPATCHER[normalized_tag](*pkgArgs)

                    else:
                        ROLES_DISPATCHER[normalized_tag](*commonArgs)

                    console.print(f"\n--- '[bold blue]{normalized_tag}[/bold blue]' role finalized for {host.name}. ---\n")
                else:
                    console_err.print(f"\n[bold yellow]WARNING:[/] Unknown tag '{normalized_tag}'. Skipping.")

def handleOrchestration(args, dry, ikwid, ROLES_DISPATCHER: DictConfig, ROLE_ALIASES: DictConfig = OmegaConf.create()):
    from pyinfra.api.connect import disconnect_all
    from pyinfra.api.exceptions import PyinfraError
    from pyinfra.api.operations import run_ops
    console = Console()
    console_err = Console(stderr=True)

    global_config, chobolo_path, secrets_file_override, sops_file_override = _get_configs(args)
    enabledSecPlugins = global_config.get('secret_plugins', [])
    userAliases = global_config.get('aliases', {})

    chobolo_config = OmegaConf.load(chobolo_path)

    state, skip = _setup_pyinfra_connection(args, chobolo_config, chobolo_path, ikwid)

    SEC_HAVING_ROLES=['users', 'secrets']
    SEC_HAVING_ROLES.extend(enabledSecPlugins)
    SEC_HAVING_ROLES = set(SEC_HAVING_ROLES)

    userAliases = _setup_user_aliases(console, userAliases, ROLE_ALIASES)

    if ROLE_ALIASES:
        ROLE_ALIASES.update(userAliases)

    decrypted_secrets = ()
    try:
        for host in state.inventory.iter_activated_hosts():
            console.print(f"\n[bold]### Applying roles to {host.name} ###[/bold]")
            commonArgs = (state, host, chobolo_path, skip)

            _run_tags(
                ROLES_DISPATCHER,
                ROLE_ALIASES,
                SEC_HAVING_ROLES,
                skip,
                decrypted_secrets,
                commonArgs,
                secrets_file_override,
                sops_file_override,
                global_config,
                args,
                console_err,
                host
            )

        if not dry:
            run_ops(state)
        else:
            console.print("[bold yellow]dry mode active, skipping.[/bold yellow]")

    except PyinfraError as e:
        console_err.print(f"[bold red]ERROR:[/] Pyinfra encountered an error: {e}")

    finally:
        console.print("\nDisconnecting...")
        disconnect_all(state)
        console.print("[bold green]Finalized.[/bold green]")

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
