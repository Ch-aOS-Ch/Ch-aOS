import logging
import os
import sys
from pathlib import Path
from typing import cast

from omegaconf import DictConfig, OmegaConf

from .args.dataclasses import SetPayload
from .boats.base import Boat
from .telemetry import ChaosTelemetry
from .utils import validate_path

"""
Orchestration/Explanation Handlers for Chaos CLI
"""


def handleVerbose(args):
    """Handle verbosity levels for logging"""
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

If the role is standard, it just calls the role function with common args.

The roles should be using pyinfra's add_op() function to queue operations, which are then executed in bulk at the end (unless dry run is active).
This allows for better performance and error handling.

I really should wrap this in a try/finally to ensure disconnection happens, but for now, this will do.
"""


def _collect_fleet_health(state, stage):
    """
    Asyncronously collects RAM and Load Average facts from all hosts in the fleet and records them in the telemetry system.

    if state.pool is available, it uses it to parallelize fact collection across hosts.
    Otherwise, it falls back to sequential collection.
    Args:
        state (State): The current pyinfra state containing the inventory and connection pool.
        stage (str): The stage of the operation (e.g., "pre_operations", "post_operations") for telemetry recording.
    """
    from .facts.facts import LoadAverage, RamUsage

    def _fetch_and_record(host):
        ram_data = host.get_fact(RamUsage)
        load_data = host.get_fact(LoadAverage)
        ChaosTelemetry.record_snapshot(host, ram_data, load_data, stage=stage)

    if state.pool:
        state.pool.map(_fetch_and_record, state.inventory.iter_activated_hosts())
    else:
        for host in state.inventory.iter_activated_hosts():
            _fetch_and_record(host)


def _resolve_limani(global_config: DictConfig, args):
    if args.limani:
        limani_name = args.limani
    else:
        limani_name = global_config.get("limani")

    if not limani_name:
        raise ValueError(
            "No Limani plugin specified.\n"
            "   Use '[cyan]--limani limani_name[/cyan]' or configure a default Limani."
        )

    return limani_name


def _get_configs(args):
    CONFIG_DIR = os.path.expanduser("~/.config/chaos")
    CONFIG_FILE_PATH = os.path.join(CONFIG_DIR, "config.yml")
    global_config = OmegaConf.create()
    if os.path.exists(CONFIG_FILE_PATH):
        global_config = OmegaConf.load(CONFIG_FILE_PATH) or OmegaConf.create()
    global_config = cast(DictConfig, global_config)

    chobolo_path = args.chobolo or global_config.get("chobolo_file", None)
    validate_path(chobolo_path)

    secrets_file_override = args.secrets_file_override or global_config.get(
        "secrets_file", None
    )
    validate_path(secrets_file_override)

    sops_file_override = args.sops_file_override or global_config.get("sops_file", None)
    validate_path(sops_file_override)

    if not chobolo_path:
        raise FileNotFoundError(
            "No Ch-obolo passed\n"
            "   Use '[cyan]-e /path/to/file.yml[/cyan]' or configure a base Ch-obolo with '[cyan]chaos set chobolo /path/to/file.yml[/cyan]'."
        )

    return global_config, chobolo_path, secrets_file_override, sops_file_override


def _load_boats() -> list[type[Boat]]:
    from importlib.metadata import EntryPoint

    from .plugDiscovery import get_plugins

    boats = get_plugins()[5]
    loaded_boat_classes = []
    if boats:
        try:
            for ep in boats.values():
                ep = cast(EntryPoint, ep)
                loaded_boat_class = ep.load()
                loaded_boat_classes.append(loaded_boat_class)
        except ImportError as e:
            print(f"Error loading boat entry points: {e}")
    return loaded_boat_classes


def _handle_boats(global_state: DictConfig, boats: list) -> DictConfig:
    from rich.console import Console

    console = Console()
    loaded_boat_classes = _load_boats()
    if not loaded_boat_classes:
        return global_state

    if not boats:
        return global_state

    for boat_config in boats:
        for boat_class in loaded_boat_classes:
            if boat_config.provider == boat_class.name:
                console.print(f"Running boat '{boat_class.name}'...")
                instance_config = boat_config.get("config", OmegaConf.create())
                boat_instance = boat_class(config=instance_config)
                try:
                    global_state = boat_instance.get_fleet(global_state)
                except Exception as e:
                    raise RuntimeError(
                        f"Boat '{boat_class.name}' failed to process fleet configuration: {e}"
                    ) from e

    return global_state


def _handle_fleet(args, chobolo_config, chobolo_path, ikwid):
    from rich.console import Console
    from rich.prompt import Confirm

    console = Console()

    isFleet = False
    if hasattr(args, "fleet") and args.fleet:
        chobolo_config = cast(DictConfig, chobolo_config)
        fleet_config = chobolo_config.get("fleet", {})

        if fleet_config:
            parallels = fleet_config.get("parallelism", 0)

            fleet_boats = fleet_config.get("boats", [])
            boat_config = _handle_boats(chobolo_config, fleet_boats).get("fleet", {})

            fleet_hosts = boat_config.get("hosts", [])

            if fleet_hosts:
                hosts = []
                container = OmegaConf.to_container(fleet_hosts, resolve=True)

                if not isinstance(container, list):
                    raise ValueError(
                        f"Fleet hosts configuration in {chobolo_path} is malformed. Expected a list of dicts of hosts."
                    )

                for host_item in container:
                    if not isinstance(host_item, dict) or len(host_item) != 1:
                        console.print(
                            f"[bold yellow]WARNING:[/] Malformed host entry in fleet configuration: {host_item}. It must be a dictionary with a single host name as the key. Skipping."
                        )
                        continue

                    hostname = list(host_item.keys())[0]
                    host_data = host_item[hostname]
                    if not isinstance(host_data, dict):
                        console.print(
                            f"[bold yellow]WARNING:[/] Malformed host data for host '{hostname}' in fleet configuration. It must be a dictionary of host parameters. Skipping."
                        )
                        continue

                    hosts.append((hostname, host_data))
                isFleet = True

                if not hosts:
                    confirm = (
                        False
                        if ikwid
                        else Confirm.ask(
                            f"[bold yellow]WARNING:[/] No valid fleet hosts found in chobolo file in {chobolo_path}, defaulting to localhost.",
                            default=False,
                        )
                    )

                    if not confirm:
                        console.print("Exiting...")
                        sys.exit(0)

                    hosts = ["@local"]
                    isFleet = False
                    parallels = 0

                return isFleet, parallels, hosts
            else:
                confirm = (
                    False
                    if ikwid
                    else Confirm.ask(
                        f"[bold yellow]WARNING:[/] No fleet hosts configured for chobolo file in {chobolo_path}, do you wish to continue? (will use localhost)",
                        default=False,
                    )
                )
                if not confirm:
                    console.print("Exiting...")
                    sys.exit(0)
                return False, 0, ["@local"]
        else:
            confirm = (
                False
                if ikwid
                else Confirm.ask(
                    f"[bold yellow]WARNING:[/] No fleet configuration found in chobolo file {chobolo_path}, do you wish to continue? (will use localhost)",
                    default=False,
                )
            )
            if not confirm:
                console.print("Exiting...")
                sys.exit(0)
            return False, 0, ["@local"]
    return False, 0, ["@local"]


def setup_hosts(args, chobolo_config, chobolo_path, ikwid):
    from pyinfra.api.inventory import Inventory  # type: ignore

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
    import time

    from rich.console import Console

    console = Console()

    from pyinfra.api.config import Config  # type: ignore
    from pyinfra.api.connect import connect_all  # type: ignore
    from pyinfra.api.state import State, StateStage  # type: ignore
    from pyinfra.context import ctx_state  # type: ignore
    # ------------------------------------

    inventory, hosts, parallels = setup_hosts(args, chobolo_config, chobolo_path, ikwid)

    config = Config(
        PARALLEL=parallels,
        DIFF=args.logbook,
    )
    state = State(inventory, config)
    state.current_stage = StateStage.Prepare

    start_time = time.time()

    if args.logbook:
        state.add_callback_handler(ChaosTelemetry())
        pyinfra_logger = logging.getLogger("pyinfra")
        pyinfra_logger.setLevel(logging.DEBUG)
        handler = ChaosTelemetry.PyinfraFactLogHandler()
        pyinfra_logger.addHandler(handler)
        ChaosTelemetry.start_run()

    ctx_state.set(state)
    sudo_password = None
    if args.sudo_password_file:
        validate_path(args.sudo_password_file)

        sudo_file = Path(args.sudo_password_file)
        if not sudo_file.exists():
            raise FileNotFoundError(f"Sudo password file not found: {sudo_file}")

        if not sudo_file.is_file():
            raise ValueError(f"Sudo password file path is not a file: {sudo_file}")

        with open(sudo_file, "r") as f:
            sudo_password = f.read().strip()

    if args.password is True:
        if not sys.stdin.isatty():
            sudo_password = sys.stdin.read().strip()
            ikwid = True
        else:
            raise ValueError(
                "'-ps' argument without value requires piped input or a value. "
                "When using pipes, ensure stdin is not a TTY (e.g., 'cat file | chaos apply -ps')."
            )
    elif args.password is not None:
        sudo_password = args.password.strip()

    if not sudo_password:
        from rich.prompt import Prompt

        sudo_password = Prompt.ask(
            "[magenta]Please, enter sudo password[/]", password=True
        )

    if not sudo_password:
        raise ValueError("Sudo password is required to proceed.")

    state.config.SUDO_PASSWORD = sudo_password

    skip = ikwid

    console.print(f"Connecting to {hosts}...")
    connect_all(state)
    console.print("[bold green]Connection established.[/bold green]")

    end_time = time.time()

    setup_duration = end_time - start_time

    if args.logbook:
        ChaosTelemetry.record_setup_phase(state, setup_duration)

    return state, skip


def _setup_user_aliases(console, userAliases: DictConfig, ROLE_ALIASES: DictConfig):
    for a in userAliases.keys():
        if a in ROLE_ALIASES:
            console.print(
                f"[bold yellow]WARNING:[/] Alias {a} already exists in Aliases installed. Skipping."
            )
            del userAliases[a]
    return userAliases


def _setup_normalized_tag(tag: str, ROLE_ALIASES: DictConfig):
    if ROLE_ALIASES:
        normalized_tag = ROLE_ALIASES.get(tag, tag)
    else:
        normalized_tag = tag
    return normalized_tag


def handleSecRoles(
    normalized_tag,
    enabledSecPlugins,
    skip,
    decrypted_secrets,
    commonArgs,
    ROLES_DISPATCHER: DictConfig,
    secrets_file_override,
    sops_file_override,
    global_config,
    args,
):
    from rich.prompt import Confirm

    if normalized_tag in enabledSecPlugins:
        confirm = (
            True
            if skip or not sys.stdin.isatty()
            else Confirm.ask(
                f"You are about to use a external plugin as Secret having plugin:\n[bold yellow]{normalized_tag}[/]\nAre you sure you want tocontinue?",
                default=False,
            )
        )
        if not confirm:
            return

    if not decrypted_secrets:
        decrypt = args.secrets
        if decrypt:
            from chaos.lib.secret_backends.utils import decrypt_secrets

            decrypted_secrets = decrypt_secrets(
                secrets_file_override, sops_file_override, global_config, args
            )

        if not decrypted_secrets:
            confirm = Confirm.ask(
                f"--secrets not passed, yet you are using a secret having role '{normalized_tag}', do you wish to decrypt and use it?",
                default=False,
            )
            if not confirm:
                return

            from chaos.lib.secret_backends.utils import decrypt_secrets

            decrypted_secrets = decrypt_secrets(
                secrets_file_override, sops_file_override, global_config, args
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
    from rich.console import Console

    console = Console()
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
                    args,
                )

            else:
                ROLES_DISPATCHER[normalized_tag](*commonArgs)

            console.print(
                f"\n--- '[bold blue]{normalized_tag}[/bold blue]' role finalized for {host.name}. ---\n"
            )
        else:
            console_err.print(
                f"\n[bold yellow]WARNING:[/] Unknown tag '{normalized_tag}'. Skipping."
            )


def handleOrchestration(
    args,
    dry,
    ikwid,
    ROLES_DISPATCHER: DictConfig,
    ROLE_ALIASES: DictConfig = OmegaConf.create(),
):
    from pyinfra.api.connect import disconnect_all  # type: ignore
    from pyinfra.api.exceptions import PyinfraError  # type: ignore
    from pyinfra.api.operations import run_ops  # type: ignore
    from rich.console import Console

    console = Console()
    console_err = Console(stderr=True)

    global_config, chobolo_path, secrets_file_override, sops_file_override = (
        _get_configs(args)
    )

    if args.logbook:
        limani = _resolve_limani(global_config, args)
        ChaosTelemetry.load_limani_plugin(
            limani, cast(dict, OmegaConf.to_container(global_config, resolve=True))
        )

    enabledSecPlugins = global_config.get("secret_plugins", [])
    userAliases = global_config.get("aliases", {})

    chobolo_config = OmegaConf.load(chobolo_path)

    state, skip = _setup_pyinfra_connection(args, chobolo_config, chobolo_path, ikwid)

    SEC_HAVING_ROLES = ["users", "secrets"]
    SEC_HAVING_ROLES.extend(enabledSecPlugins)
    SEC_HAVING_ROLES = set(SEC_HAVING_ROLES)

    userAliases = _setup_user_aliases(console, userAliases, ROLE_ALIASES)

    if ROLE_ALIASES:
        ROLE_ALIASES.update(userAliases)

    decrypted_secrets = ()
    run_status = "success"
    try:
        if args.logbook:
            _collect_fleet_health(state, stage="pre_operations")

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
                host,
            )

        if not dry:
            run_ops(state, args.serial, args.no_wait)
            if args.logbook:
                _collect_fleet_health(state, stage="post_operations")
        else:
            console.print("[bold yellow]dry mode active, skipping.[/bold yellow]")

    except PyinfraError as e:
        run_status = "failure"
        console_err.print(f"[bold red]ERROR:[/] Pyinfra encountered an error: {e}")

    finally:
        if args.logbook:
            if args.export_logs:
                ChaosTelemetry.export_report()
            ChaosTelemetry.end_run(status=run_status)

        console.print("\nDisconnecting...")
        disconnect_all(state)
        console.print("[bold green]Finalized.[/bold green]")


def setMode(payload: SetPayload):
    """
    Just handles configuring the tool.
    """
    CONFIG_DIR = os.path.expanduser("~/.config/chaos")
    CONFIG_FILE_PATH = os.path.join(CONFIG_DIR, "config.yml")

    print(f"Saving configuration to {CONFIG_FILE_PATH}...")

    os.makedirs(CONFIG_DIR, exist_ok=True)

    if os.path.exists(CONFIG_FILE_PATH):
        global_config = OmegaConf.load(CONFIG_FILE_PATH)
    else:
        global_config = OmegaConf.create()

    if hasattr(payload, "chobolo_file") and payload.chobolo_file:
        inputPath = Path(payload.chobolo_file)
        try:
            absolutePath = inputPath.resolve(strict=True)
            global_config.chobolo_file = str(absolutePath)
            print(f"- Default Ch-obolo set to: {payload.chobolo_file}")
        except FileNotFoundError:
            raise FileNotFoundError(f"ERROR: File not found in: {inputPath}")

    if hasattr(payload, "secrets_file") and payload.secrets_file:
        inputPath = Path(payload.secrets_file)
        try:
            absolutePath = inputPath.resolve(strict=True)
            global_config.secrets_file = str(absolutePath)
            print(f"- Default secrets file set to: {payload.secrets_file}")
        except FileNotFoundError:
            raise FileNotFoundError(f"ERROR: File not found in: {inputPath}")

    if hasattr(payload, "sops_file") and payload.sops_file:
        inputPath = Path(payload.sops_file)
        try:
            absolutePath = inputPath.resolve(strict=True)
            global_config.sops_file = str(absolutePath)
            print(f"- Default sops file set to: {payload.sops_file}")
        except FileNotFoundError:
            raise FileNotFoundError(f"ERROR: File not found in: {inputPath}")

    OmegaConf.save(global_config, CONFIG_FILE_PATH)
    print("Configuration saved.")
