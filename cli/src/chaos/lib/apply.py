from typing import Any

from omegaconf import DictConfig

from chaos.lib.args.dataclasses import (
    ApplyPayload,
    DataGatherPayload,
    DataGatherRequest,
    Delta,
    ResultPayload,
)
from chaos.lib.boats.base import Boat
from chaos.lib.roles.role import Role


def handle_verbose(payload: ApplyPayload) -> None:
    """Handle verbosity levels for logging"""
    import logging

    log_level = None
    if payload.verbose:
        if payload.verbose == 1:
            log_level = logging.WARNING
        elif payload.verbose == 2:
            log_level = logging.INFO
        elif payload.verbose == 3:
            log_level = logging.DEBUG
    elif payload.v == 1:
        log_level = logging.WARNING
    elif payload.v == 2:
        log_level = logging.INFO
    elif payload.v == 3:
        log_level = logging.DEBUG

    if log_level:
        logging.basicConfig(level=log_level, format="%(levelname)s: %(message)s")


def gather_apply(
    payload: ApplyPayload,
) -> tuple[DataGatherRequest | None, ResultPayload | None, dict[str, Role] | None]:
    i_know, sudo_password = _handle_password(payload, payload.i_know_what_im_doing)
    request = DataGatherRequest(name="apply", fields=[])
    result = ResultPayload(success=True, message=[], error=[], data={})
    if not sudo_password:
        request.fields.append(
            DataGatherPayload(
                prompt="Please, enter your sudo password:",
                name="sudo_password",
                input_type="secret",
                required=True,
            )
        )
    else:
        result.data["sudo_password"] = sudo_password

    try:
        loaded_roles = _load_role_eps(payload.tags)
    except ValueError as e:
        result.success = False
        result.error.append(str(e))
        return None, result, None

    roles_that_need_secrets = []
    secrets_needed = []

    for role in payload.tags:
        if role not in loaded_roles:
            result.success = False
            result.error.append(f"Role '{role}' could not be loaded.")
            continue

        role_class = loaded_roles[role]

        if role_class.needs_secrets and not i_know:
            if not role_class.necessary_secret_dict_keys:
                result.success = False
                result.error.append(
                    f"Role '{role}' requires secrets but does not specify necessary_secret_dict_keys."
                )
                continue

            roles_that_need_secrets.append(role)
            secrets_needed.extend(role_class.necessary_secret_dict_keys)

    if roles_that_need_secrets and not i_know and not payload.secrets:
        request.fields.append(
            DataGatherPayload(
                prompt=f"""The Role(s) {", ".join(roles_that_need_secrets)} require secrets.
They need the following keys: {", ".join(secrets_needed)}
Do you want to provide them?""",
                name="role_secrets",
                input_type="boolean",
                required=True,
                default=False,
            )
        )

    return request, result, loaded_roles


def gather_fleet(
    payload: ApplyPayload, chobolo_config, chobolo_path: str
) -> tuple[DataGatherRequest | None, ResultPayload]:
    from typing import cast

    from omegaconf import OmegaConf

    if not payload.fleet:
        return None, ResultPayload(
            success=True, data={"hosts": ["@local"], "is_fleet": False, "parallels": 0}
        )

    chobolo_config = cast(DictConfig, chobolo_config)
    fleet_config = chobolo_config.get("fleet", {})

    if not fleet_config:
        if payload.i_know_what_im_doing:
            return None, ResultPayload(
                success=True,
                data={"hosts": ["@local"], "is_fleet": False, "parallels": 0},
            )

        request = DataGatherRequest(
            name="fleet_fallback",
            fields=[
                DataGatherPayload(
                    prompt=f"No fleet configuration found in {chobolo_path}. Do you wish to continue with localhost?",
                    name="fallback_to_local",
                    input_type="boolean",
                    default=False,
                )
            ],
        )
        return request, ResultPayload(success=True, data={})

    parallels = fleet_config.get("parallelism", 0)
    fleet_boats = fleet_config.get("boats", [])

    try:
        boat_config = _handle_boats(chobolo_config, fleet_boats).get("fleet", {})
    except Exception as e:
        return None, ResultPayload(success=False, error=[str(e)])

    fleet_hosts = boat_config.get("hosts", [])

    if not fleet_hosts:
        if payload.i_know_what_im_doing:
            return None, ResultPayload(
                success=True,
                data={"hosts": ["@local"], "is_fleet": False, "parallels": 0},
            )

        request = DataGatherRequest(
            name="fleet_fallback",
            fields=[
                DataGatherPayload(
                    prompt=f"No fleet hosts configured for chobolo file in {chobolo_path}. Do you wish to continue? (will use localhost)",
                    name="fallback_to_local",
                    input_type="boolean",
                    default=False,
                )
            ],
        )
        return request, ResultPayload(success=True, data={})

    hosts = []
    container = OmegaConf.to_container(fleet_hosts, resolve=True)

    if not isinstance(container, list):
        return None, ResultPayload(
            success=False,
            error=[
                f"Fleet hosts configuration in {chobolo_path} is malformed. Expected a list of dicts of hosts."
            ],
        )

    messages = []
    for host_item in container:
        if not isinstance(host_item, dict) or len(host_item) != 1:
            messages.append(
                f"Malformed host entry in fleet configuration: {host_item}. It must be a dictionary with a single host name as the key. Skipping."
            )
            continue

        hostname = list(host_item.keys())[0]
        host_data = host_item[hostname]
        if not isinstance(host_data, dict):
            messages.append(
                f"Malformed host data for host '{hostname}' in fleet configuration. It must be a dictionary of host parameters. Skipping."
            )
            continue

        hosts.append((hostname, host_data))

    if not hosts:
        if payload.i_know_what_im_doing:
            return None, ResultPayload(
                success=True,
                data={"hosts": ["@local"], "is_fleet": False, "parallels": 0},
            )

        request = DataGatherRequest(
            name="fleet_fallback",
            fields=[
                DataGatherPayload(
                    prompt=f"No valid fleet hosts found in chobolo file in {chobolo_path}, default to localhost?",
                    name="fallback_to_local",
                    input_type="boolean",
                    default=False,
                )
            ],
        )
        return request, ResultPayload(success=True, message=messages, data={})

    return None, ResultPayload(
        success=True,
        message=messages,
        data={"hosts": hosts, "is_fleet": True, "parallels": parallels},
    )


def run_context(payload: ApplyPayload, role: Role, host) -> ResultPayload:
    from omegaconf import OmegaConf

    global_config, chobolo_path, secrets_file_override, sops_file_override = (
        _get_configs(payload)
    )

    if role.needs_secrets and not payload.secrets:
        return ResultPayload(
            success=False,
            message=[],
            error=[f"Role '{role}' requires secrets but none were provided."],
            data={},
        )

    chobolo_data = (
        OmegaConf.load(chobolo_path).to_container()
        if chobolo_path
        else OmegaConf.create()
    )

    chobolo_for_role = {
        key: chobolo_data[key]
        for key in role.necessary_chobolo_keys
        if key in chobolo_data
    }

    secrets_for_role = {}

    secrets_result, secrets_dict = _handle_secrets_for_role(
        role, payload, secrets_file_override, sops_file_override, global_config
    )

    if not secrets_result["success"]:
        return ResultPayload(
            success=False,
            message=[],
            error=[
                f"Role '{role}' requires secrets but they could not be loaded: {secrets_result['error']}"
            ],
            data={},
        )

    secrets_for_role: dict[str, Any] = secrets_dict

    context = role.get_context(
        payload.pyinfra_state, host, chobolo_for_role, secrets_for_role
    )

    return ResultPayload(success=True, message=[], error=[], data=context)


def run_delta(
    context: dict[str, Any], role: Role, role_name: str
) -> tuple[ResultPayload, Delta]:
    try:
        delta: Delta = role.delta(context)
    except Exception as e:
        return ResultPayload(
            success=False,
            message=[],
            error=[f"Error computing delta for role '{role_name}': {str(e)}"],
            data={},
        ), Delta(to_add={}, to_remove={})
    return ResultPayload(success=True, message=[], error=[], data={}), delta


def run_plan(
    payload: ApplyPayload,
    delta: Delta,
    role: Role,
    role_name: str,
    host,
    restrictions: dict[str, dict[str, dict[str, bool]]],
) -> ResultPayload:
    black_list = restrictions.get("black_list", {})
    allow_list = restrictions.get("allow_list", {})

    in_allow = allow_list.get(host, {}).get(role_name, False)
    in_black = black_list.get(host, {}).get(role_name, False)

    if in_allow and in_black:
        return ResultPayload(
            success=False,
            message=[],
            error=[
                f"Role '{role_name}' is both blacklisted and allowlisted for host '{host}'. Please resolve this conflict in your configuration."
            ],
            data={},
        )

    if in_black and not in_allow:
        return ResultPayload(
            success=True,
            message=[],
            error=[f"Role '{role_name}' is blacklisted for host '{host}'."],
            data={},
        )

    if (
        host in black_list
        and not black_list.get(host, {})
        and not allow_list.get(host, {})
    ):
        return ResultPayload(
            success=True,
            message=[],
            error=[f"Host '{host}' is completely blacklisted."],
            data={},
        )

    try:
        plan = role.plan(payload.pyinfra_state, host, delta)
    except Exception as e:
        return ResultPayload(
            success=False,
            message=[],
            error=[f"Error computing plan for role '{role_name}': {str(e)}"],
            data={},
        )
    return ResultPayload(success=True, message=[], error=[], data={"plan": plan})


def _setup_pyinfra(payload: ApplyPayload) -> ApplyPayload:
    import logging
    import time

    from pyinfra.api.config import Config  # type: ignore
    from pyinfra.api.connect import connect_all  # type: ignore
    from pyinfra.api.state import State, StateStage  # type: ignore
    from pyinfra.context import ctx_state  # type: ignore

    from .telemetry import ChaosTelemetry

    inventory, _, parallels = _setup_hosts(payload)

    config = Config(
        PARALLEL=parallels,
        DIFF=payload.logbook,
    )

    state = State(inventory, config)
    state.current_stage = StateStage.Prepare

    start_time = time.time()

    if payload.logbook:
        state.add_callback_handler(ChaosTelemetry())
        pyinfra_logger = logging.getLogger("pyinfra")
        pyinfra_logger.setLevel(logging.DEBUG)
        handler = ChaosTelemetry.PyinfraFactLogHandler()
        pyinfra_logger.addHandler(handler)
        ChaosTelemetry.start_run()

    ctx_state.set(state)

    sudo_password = payload.confirmed_password
    state.config.SUDO_PASSWORD = sudo_password

    connect_all(state)

    end_time = time.time()
    setup_duration = end_time - start_time

    if payload.logbook:
        ChaosTelemetry.record_setup_phase(state, setup_duration)

    payload.pyinfra_state = state

    return payload


def _load_boats() -> list[type[Boat]]:
    from importlib.metadata import EntryPoint
    from typing import cast

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
            raise ImportError(f"failed to load boat plugin: {e}")
    return loaded_boat_classes


def _handle_boats(global_state, boats: list) -> DictConfig:
    from omegaconf import OmegaConf

    loaded_boat_classes = _load_boats()
    if not loaded_boat_classes:
        return global_state

    if not boats:
        return global_state

    for boat_config in boats:
        for boat_class in loaded_boat_classes:
            if boat_config.provider == boat_class.name:
                instance_config = boat_config.get("config", OmegaConf.create())
                boat_instance = boat_class(config=instance_config)
                try:
                    global_state = boat_instance.get_fleet(global_state)
                except Exception as e:
                    raise RuntimeError(
                        f"Boat '{boat_class.name}' failed to process fleet configuration: {e}"
                    ) from e

    return global_state


def _setup_hosts(payload: ApplyPayload):
    from pyinfra.api.inventory import Inventory  # type: ignore

    if not payload.is_fleet_active:
        inventory = Inventory((payload.target_hosts, {}))
    else:
        inventory = Inventory(payload.target_hosts)

    return inventory, payload.target_hosts, payload.parallelism


def _get_configs(payload: ApplyPayload):
    import os
    from typing import cast

    from omegaconf import OmegaConf

    from .utils import validate_path

    CONFIG_DIR = os.path.expanduser("~/.config/chaos")
    CONFIG_FILE_PATH = os.path.join(CONFIG_DIR, "config.yml")
    global_config = OmegaConf.create()
    if os.path.exists(CONFIG_FILE_PATH):
        global_config = OmegaConf.load(CONFIG_FILE_PATH) or OmegaConf.create()
    global_config = cast(DictConfig, global_config)

    chobolo_path = payload.chobolo or global_config.get("chobolo_file", None)
    validate_path(chobolo_path)

    secrets_file_override = (
        payload.secrets_context.secrets_file_override
        or global_config.get("secrets_file", None)
    )
    validate_path(secrets_file_override)

    sops_file_override = (
        payload.secrets_context.sops_file_override
        or global_config.get("sops_file", None)
    )
    validate_path(sops_file_override)

    if not chobolo_path:
        raise FileNotFoundError(
            "No Ch-obolo passed\n"
            "   Use '-e /path/to/file.yml' or configure a base Ch-obolo with 'chaos set chobolo /path/to/file.yml'."
        )

    return global_config, chobolo_path, secrets_file_override, sops_file_override


def _handle_secrets_for_role(
    role: Role,
    payload: ApplyPayload,
    secrets_file_override: str,
    sops_file_override: str,
    global_config,
) -> tuple[dict[str, bool | str], dict[str, Any]]:
    if role.needs_secrets and payload.secrets:
        from omegaconf import OmegaConf

        from chaos.lib.secret_backends.utils import decrypt_secrets

        try:
            decrypted_secrets = decrypt_secrets(
                secrets_file_override,
                sops_file_override,
                global_config,
                payload.secrets_context,
            )
        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to decrypt secrets: {str(e)}",
            }, {}

        if not decrypted_secrets:
            return {"success": False, "error": "No secrets were decrypted."}, {}

        loaded_secrets = OmegaConf.create(decrypted_secrets).to_container()
        secrets_for_role = {
            key: loaded_secrets[key]
            for key in role.necessary_secret_dict_keys
            if key in loaded_secrets
        }
        return {"success": True}, secrets_for_role
    return {"success": True}, {}


def _handle_password(payload: ApplyPayload, ikwid: bool) -> tuple[bool, str | None]:
    import sys
    from pathlib import Path

    from .utils import validate_path

    sudo_password = None
    i_know = ikwid
    if payload.sudo_password_file:
        validate_path(payload.sudo_password_file)

        sudo_file = Path(payload.sudo_password_file)
        if not sudo_file.exists():
            raise FileNotFoundError(f"Sudo password file not found: {sudo_file}")

        if not sudo_file.is_file():
            raise ValueError(f"Sudo password file path is not a file: {sudo_file}")

        with open(sudo_file, "r") as f:
            sudo_password = f.read().strip()

    if payload.password:
        if not sys.stdin.isatty():
            sudo_password = sys.stdin.read().strip()
            ikwid = True
        else:
            sudo_password = payload.password
    elif payload.password is not None:
        sudo_password = payload.password.strip()

    return i_know, sudo_password


def _load_role_eps(role_names: list[str]) -> dict[str, Role]:
    from chaos.lib.utils import get_roleEps

    role_eps = get_roleEps()
    loaded_roles = {}
    for role_name in role_names:
        matching_eps = [ep for ep in role_eps if ep.name == role_name]
        if not matching_eps:
            raise ValueError(f"Role '{role_name}' not found among available plugins.")
        elif len(matching_eps) > 1:
            raise ValueError(
                f"Multiple plugins found for role '{role_name}'. Please specify a unique name."
            )
        else:
            loaded_roles[role_name] = matching_eps[0].load()
    return loaded_roles
