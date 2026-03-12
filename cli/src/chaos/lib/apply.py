from typing import TYPE_CHECKING, Any

from omegaconf import DictConfig, ListConfig

if TYPE_CHECKING:
    from pyinfra.api.host import Host

    from chaos.lib.args.dataclasses import (
        ApplyPayload,
        DataGatherPayload,
        DataGatherRequest,
        Delta,
        ResultPayload,
    )
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
) -> tuple[DataGatherRequest | None, ResultPayload | None]:
    """
    Gather necessary data for applying roles, such as sudo password and secrets if needed.

    parameters:
        payload: the ApplyPayload containing the initial data and flags for the apply operation.

    returns:
        - A DataGatherRequest if additional data needs to be gathered from the user, or None
        - A ResultPayload indicating the success or failure of the data gathering process, or None if a DataGatherRequest is returned.
        - A dictionary of loaded Role classes keyed by their names if data gathering is successful, or None if a DataGatherRequest is
            returned or if there was an error loading the roles.
    """

    sudo_password_result = _handle_password(payload)
    if not sudo_password_result.success:
        return None, sudo_password_result

    sudo_password = sudo_password_result.data

    request = DataGatherRequest(name="apply", fields=[])
    result = ResultPayload(success=True, message=[], error=[], data={})
    i_know = payload.i_know_what_im_doing

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

    result_load = _load_role_eps(payload.tags)
    if not result_load.success:
        return request, result_load

    loaded_roles = result_load.data

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

    global_config, result = _get_configs(payload)
    payload.global_config = global_config.to_container()

    if not result.success:
        return None, ResultPayload(
            success=False,
            message=[],
            error=[f"Error loading global configuration: {result.error}"],
            data={},
        )

    result.data["loaded_roles"] = loaded_roles
    if not request.fields:
        return None, result
    return request, result


def gather_fleet(
    payload: ApplyPayload, chobolo_config: DictConfig, chobolo_path: str
) -> tuple[DataGatherRequest | None, ResultPayload]:
    """
    Gather necessary data for fleet configuration, such as host information and parallelism settings.

    parameters:
        - payload: the ApplyPayload containing the initial data and flags for the apply operation.
        - chobolo_config: the loaded chobolo configuration as a DictConfig object.
        - chobolo_path: the file path to the chobolo configuration file, used
            for error messages and prompts to the user when gathering data.

    returns:
        - A DataGatherRequest if additional data needs to be gathered from the user, or None
        - A ResultPayload indicating the success or failure of the data gathering process, with relevant data about
             the fleet configuration if successful.
    """

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
        boat_config, result = _handle_boats(chobolo_config, fleet_boats)
        if not result.success:
            return None, ResultPayload(
                success=False,
                error=[
                    f"Error processing boats for fleet configuration: {result.error}"
                ],
            )

        boat_config = boat_config.get("fleet", {}) if boat_config else {}
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


def run_context(payload: ApplyPayload, role: Role, host: Host) -> ResultPayload:
    """
    Run the context method for a given role and host, gathering necessary configuration and secrets.

    parameters:
        - payload: the ApplyPayload containing the initial data and flags for the apply operation.
        - role: the Role class for which to run the context method.
        - host: the Host object representing the target host for which to gather context.

    returns:
        - A ResultPayload indicating the success or failure of the context gathering process, with the gathered context data if successful.
            the context data is inside of the ResultPayload.data field, and any error messages are in the error field.
    """

    from omegaconf import OmegaConf

    chobolo_path = payload.global_config.get("chobolo_path", None)

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

    chobolo_for_role = {}
    for key in role.necessary_chobolo_keys:
        value = OmegaConf.select(chobolo_data, key, default=None)
        if value is None:
            return ResultPayload(
                success=False,
                message=[],
                error=[
                    f"Role '{role}' requires chobolo key '{key}' which was not found in the chobolo data."
                ],
                data={},
            )
        chobolo_for_role[key] = value

    secrets_for_role = {}

    secrets_result = _handle_secrets_for_role(role, payload)

    if not secrets_result.success:
        return ResultPayload(
            success=False,
            message=[],
            error=[
                f"Role '{role}' requires secrets but they could not be loaded: {secrets_result.error}"
            ],
            data={},
        )

    secrets_for_role: dict[str, Any] = secrets_result.data

    context = role.get_context(
        payload.pyinfra_state, host, chobolo_for_role, secrets_for_role
    )

    return ResultPayload(success=True, message=[], error=[], data=context)


def run_delta(
    context: dict[str, Any], role: Role, role_name: str
) -> tuple[ResultPayload, Delta]:
    """
    Run the delta method for a given role and context, computing the necessary changes to apply the role.

    parameters:
        - context: the context data gathered for the role, which should contain all necessary information for computing the delta.
            this should be the data returned in the ResultPayload.data field from the run_context function.
        - role: the Role class for which to run the delta method.
        - role_name: the name of the role, used for error messages.

    returns:
        - A ResultPayload indicating the success or failure of the delta computation process, with any error
            messages in the error field.

        - A Delta object representing the changes that need to be applied for the role, if the
            computation was successful. If there was an error, this will be an empty Delta with no changes.
    """

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
    host: Host,
    restrictions: dict[str, dict[str, dict[str, bool]]],
) -> ResultPayload:
    """
    Runs the plan method for a given role and host, computing the necessary
        operations to apply the role, while also checking against any allowlist or blacklist restrictions for the role and host.

    parameters:
        - payload: the ApplyPayload containing the initial data and flags for the apply operation.
        - delta: the Delta object representing the changes that need to be applied for the role, which should be the output from
            the run_delta function. this should be the data returned in the ResultPayload.data field from the run_delta function.
        - role: the Role class for which to run the plan method.
        - role_name: the name of the role, used for error messages and checking restrictions.
        - host: the Host object representing the target host for which to compute the plan.
        - restrictions: a dictionary containing any allowlist or blacklist restrictions for roles and hosts, used
            to determine if the role should be applied to the host or if there are any conflicts in the configuration.

            This dictionary should be inside of the chobolo file, and should have the following structure:
                restrictions:
                    black_list:
                        host1:
                            role1: true
                            role2: true
                        host2:
                            role3: true

                    allow_list:
                        host1:
                            role3: true
                        host3:
                            role1: true
                            role4: true

        - The function will check the restrictions in the following order:
            1. A conflict check to see if the role is both blacklisted and allowlisted for the host, which will result in an error.
            2. A check to see if the role is blacklisted for the host, which will skip the role for that host.
            3. A check to see if the host is completely blacklisted (if it is host: {} and not in an allow_list), which will skip all roles
                for that host.
            4. A check to see if the host is allowlisted but the role is not on the allowlist, which will skip it.

    returns:
        - A ResultPayload indicating the success or failure of the plan computation process, with any error
            messages in the error field, and the computed plan in the data field if successful.
            The plan should be the data returned from the role.plan() method if all checks pass and the plan is computed successfully.
            If there are any errors or if the role is skipped due to restrictions, the plan will not be included in the data field.
    """

    black_list = restrictions.get("black_list", {})
    allow_list = restrictions.get("allow_list", {})

    in_allow = allow_list.get(host.name, {}).get(role_name, False)
    in_black = black_list.get(host.name, {}).get(role_name, False)

    if in_allow and in_black:
        return ResultPayload(
            success=False,
            message=[],
            error=[
                f"Role '{role_name}' is both blacklisted and allowlisted for host '{host.name}'. Please resolve this conflict in your configuration."
            ],
            data={},
        )

    if in_black and not in_allow:
        return ResultPayload(
            success=True,
            message=[],
            error=[f"Role '{role_name}' is blacklisted for host '{host.name}'."],
            data={},
        )

    if (
        host.name in black_list
        and not black_list.get(host.name, {})
        and not allow_list.get(host.name, {})
    ):
        return ResultPayload(
            success=True,
            message=[],
            error=[f"Host '{host.name}' is completely blacklisted."],
            data={},
        )

    if host.name in allow_list and not in_allow:
        return ResultPayload(
            success=True,
            message=[],
            error=[
                f"Host '{host.name}' is allowlisted but role '{role_name}' is not on the allowlist."
            ],
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


def resolve_alias(payload: ApplyPayload) -> ResultPayload:
    """
    Resolves any aliases in the payload tags based on the plugin aliases and user configuration aliases,
         while also checking for circular references and conflicts.
    """

    from .plugDiscovery import get_plugins

    warnings = []

    plug_aliases = get_plugins()[1]
    user_config = payload.global_config
    user_aliases = user_config.get("aliases", {}) if user_config else {}

    merged_aliases = {}
    if plug_aliases:
        merged_aliases.update(plug_aliases)

    if user_aliases:
        for k, v in user_aliases.items():
            if k in merged_aliases:
                warnings.append(
                    f"Alias '{k}' from user configuration overrides plugin alias."
                )
            merged_aliases[k] = v

    resolved_tags = []
    seen_aliases = set()

    def _resolve_alias(tag: str, local_seen: set) -> None:
        if tag in local_seen:
            if tag not in resolved_tags:
                resolved_tags.append(tag)

            if len(local_seen) > 1:
                warnings.append(
                    f"Circular alias detected for '{tag}'. Skipping to prevent infinite loop."
                )
            return
        if tag in merged_aliases:
            new_seen = local_seen | {tag}
            if tag in seen_aliases:
                warnings.append(
                    f"Duplicate alias '{tag}' specified in tags. Only the first occurrence will be used."
                )
                return

            seen_aliases.add(tag)
            target = merged_aliases[tag]

            if isinstance(target, str):
                targets = target.split(" ")

            elif isinstance(target, (list, tuple)):
                targets = list(target)

            else:
                warnings.append(
                    f"Alias '{tag}' has an invalid target type: {type(target)}. Skipping."
                )

                targets = []

            for t in targets:
                _resolve_alias(t, local_seen=new_seen)

            seen_aliases.remove(tag)

        else:
            if tag not in resolved_tags:
                resolved_tags.append(tag)

    for tag in payload.tags:
        _resolve_alias(tag, local_seen=set())

    return ResultPayload(success=True, message=warnings, error=[], data=resolved_tags)


def _setup_pyinfra(payload: ApplyPayload) -> ApplyPayload:
    """
    Set up the pyinfra state and inventory based on the gathered fleet configuration, and establish connections to the target hosts.

    parameters:
        - payload: the ApplyPayload containing the gathered data for the apply operation, including fleet configuration and sudo password.

    returns:
        - The updated ApplyPayload with the pyinfra state set up and ready for executing plans. The pyinfra state will be stored in the
             payload.pyinfra_state field for use in subsequent steps of the apply process.
    """

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


def _load_boats(necessary_boats: set[str]) -> ResultPayload:
    """
    Loads boat plugins using the importlib metadata entry points, specifically looking for plugins under "chaos.boats"
        It attempts to load all boat plugins and returns a list of the loaded boat classes.

    This function is lazy and only loads boats that are necessary.

    parameters:
        - necessary_boats: a set of boat provider names that are needed for the fleet configuration.
             Only boats with providers in this set will be loaded.
    returns:
        - A ResultPayload indicating the success or failure of the boat loading process,
            with any error messages in the error field, and a list of loaded boat classes in the data field if successful.
    """

    from importlib.metadata import EntryPoint
    from typing import cast

    from .plugDiscovery import get_plugins

    all_boats = get_plugins()[5]
    loaded_boat_classes = []
    if not all_boats:
        return ResultPayload(success=True, message=[], error=[], data=[])
    for boat_name in necessary_boats:
        if boat_name not in all_boats:
            return ResultPayload(
                success=False,
                message=[],
                error=[f"No plugin found for boat provider '{boat_name}'."],
                data=[],
            )

        try:
            ep = cast(EntryPoint, all_boats[boat_name])
            loaded_boat_class = ep.load()
            loaded_boat_classes.append(loaded_boat_class)
        except ImportError as e:
            return ResultPayload(
                success=False,
                message=[],
                error=[
                    f"Error loading plugin for boat provider '{boat_name}': {str(e)}"
                ],
                data=[],
            )
    return ResultPayload(success=True, message=[], error=[], data=loaded_boat_classes)


def _handle_boats(
    global_state: DictConfig, boats: ListConfig
) -> tuple[DictConfig, ResultPayload]:

    from omegaconf import OmegaConf

    necessary_boats = set()
    for boat in boats:
        provider = boat.get("provider", None)
        if provider:
            necessary_boats.add(provider)

    result = _load_boats(necessary_boats)

    loaded_boat_classes = result.data if result.success else []

    if not result.success:
        return global_state, result

    if not loaded_boat_classes:
        return global_state, ResultPayload(success=True, message=[], error=[])

    if not boats:
        return global_state, ResultPayload(success=True, message=[], error=[])

    for boat_config in boats:
        for boat_class in loaded_boat_classes:
            if boat_config.provider == boat_class.name:
                instance_config = boat_config.get("config", OmegaConf.create())
                boat_instance = boat_class(config=instance_config)
                try:
                    global_state = boat_instance.get_fleet(global_state)
                except Exception as e:
                    return global_state, ResultPayload(
                        success=False,
                        message=[],
                        error=[f"Error processing boat '{boat_class.name}': {str(e)}"],
                    )

    return global_state, ResultPayload(success=True, message=[], error=[])


def _setup_hosts(payload: ApplyPayload) -> tuple[Any, list[tuple[str, dict]], int]:
    """
    Sets up the inventory of hosts for pyinfra based on the fleet configuration gathered from the chobolo file,
         and determines the parallelism settings for executing plans on the fleet.

    parameters:
        - payload: the ApplyPayload containing the gathered data for the apply operation, including fleet configuration
            such as the list of target hosts and parallelism settings.

    returns:
        - An inventory object compatible with pyinfra, constructed based on the target hosts specified in the payload.
        - A list of tuples representing the target hosts and their associated data, extracted from the payload
        - An integer representing the parallelism settings for executing plans on the fleet, extracted from the payload.
    """
    from pyinfra.api.inventory import Inventory  # type: ignore

    if not payload.is_fleet_active:
        inventory = Inventory((payload.target_hosts, {}))
    else:
        inventory = Inventory(payload.target_hosts)

    return inventory, payload.target_hosts, payload.parallelism


def _get_configs(payload: ApplyPayload) -> tuple[DictConfig, ResultPayload]:
    """
    Loads global configuration from a chobolo file and validates paths for chobolo,
         secrets file, and sops file based on the payload and global configuration.

    parameters:
        - payload: the ApplyPayload containing any overrides for configuration paths,
             such as chobolo file path, secrets file path, and sops file path.

    returns:
        - A DictConfig object representing the loaded global configuration, which may include overrides from the payload.
        - A ResultPayload indicating the success or failure of the configuration loading and validation process, with
            any error messages in the error field, and the relevant configuration data (such as validated paths) in
            the data field if successful.
    """

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
    try:
        validate_path(chobolo_path)
    except Exception as e:
        return global_config, ResultPayload(
            success=False,
            message=[],
            error=[f"Error with chobolo file path: {str(e)}"],
            data={},
        )

    secrets_file_override = (
        payload.secrets_context.secrets_file_override
        or global_config.get("secrets_file", None)
    )
    try:
        validate_path(secrets_file_override)
    except Exception as e:
        return global_config, ResultPayload(
            success=False,
            message=[],
            error=[f"Error with secrets file path: {str(e)}"],
            data={},
        )

    sops_file_override = (
        payload.secrets_context.sops_file_override
        or global_config.get("sops_file", None)
    )
    try:
        validate_path(sops_file_override)
    except Exception as e:
        return global_config, ResultPayload(
            success=False,
            message=[],
            error=[f"Error with sops file path: {str(e)}"],
            data={},
        )

    if not chobolo_path:
        return (
            global_config,
            ResultPayload(
                success=False,
                message=[],
                error=["No chobolo file specified in payload or global config."],
                data={},
            ),
        )

    return global_config, ResultPayload(
        success=True,
        message=[],
        error=[],
        data={
            "chobolo_path": chobolo_path,
            "secrets_file_override": secrets_file_override,
            "sops_file_override": sops_file_override,
        },
    )


def _handle_secrets_for_role(
    role: Role,
    payload: ApplyPayload,
    role_name: str = "",
) -> ResultPayload:
    """
    Handles the loading and decryption of secrets for a given role based on the payload and global configuration.

    parameters:
        - role: the Role class for which to handle secrets, used to determine if secrets are needed and what keys are necessary.
        - payload: the ApplyPayload containing any overrides for secrets file path and sops file path, as well as the secrets context.
        - secrets_file_override: the path to the secrets file, determined from the payload or global configuration, used for loading secrets.
        - sops_file_override: the path to the sops file, determined from the payload or global configuration, used for decrypting secrets
             if they are encrypted with sops.
        - global_config: the loaded global configuration, which may contain additional context needed for decrypting secrets.

    returns:
        - A ResultPayload indicating the success or failure of the secrets handling process, with any error messages in the error field,
            and a dictionary of secrets for the role in the data field if successful. The secrets for the role will be filtered based on the
            necessary_secret_dict_keys specified by the role, and will only include those keys that are present in the loaded secrets.
    """

    decrypted_secrets = payload.decrypted_secrets

    if role.needs_secrets and payload.secrets:
        from omegaconf import OmegaConf

        if not decrypted_secrets:
            return ResultPayload(
                success=False,
                message=[],
                error=["No secrets could be decrypted."],
                data={},
            )

        loaded_secrets_conf = OmegaConf.create(decrypted_secrets)
        secrets_for_role = {}
        for key in role.necessary_secret_dict_keys:
            value = OmegaConf.select(loaded_secrets_conf, key, default=None)
            if value is None:
                return ResultPayload(
                    success=False,
                    message=[],
                    error=[
                        f"Role '{role_name}' requires secret key '{key}' which was not found in the decrypted secrets."
                    ],
                    data={},
                )

            if isinstance(value, (DictConfig, ListConfig)):
                secrets_for_role[key] = OmegaConf.to_container(value, resolve=True)
            else:
                secrets_for_role[key] = value

        return ResultPayload(success=True, message=[], error=[], data=secrets_for_role)
    return ResultPayload(success=True, message=[], error=[], data={})


def _handle_password(payload: ApplyPayload) -> ResultPayload:
    """
    Handles the retrieval of the sudo password based on the payload, either from a specified file or directly from the payload.

    parameters:
        - payload: the ApplyPayload containing any overrides for the sudo password file path or the password itself.

    returns:
        - A ResultPayload indicating the success or failure of the password retrieval process, with any error messages in the error field,
            and the retrieved sudo password in the data field if successful. The function will first check if a sudo password file is
            specified and attempt to read the password from that file, validating the path and ensuring it is a file. If no file is specified,
            it will check if a password is directly provided in the payload and use that. If neither is provided,
            it will return an empty string as the password.
    """

    from pathlib import Path

    from .utils import validate_path

    sudo_password = ""
    if payload.sudo_password_file:
        try:
            validate_path(payload.sudo_password_file)
        except Exception as e:
            return ResultPayload(
                success=False,
                message=[],
                error=[f"Error with sudo password file path: {str(e)}"],
                data={},
            )

        sudo_file = Path(payload.sudo_password_file)
        if not sudo_file.exists():
            return ResultPayload(
                success=False,
                message=[],
                error=[f"Sudo password file not found: {sudo_file}"],
                data={},
            )

        if not sudo_file.is_file():
            return ResultPayload(
                success=False,
                message=[],
                error=[f"Sudo password file path is not a file: {sudo_file}"],
                data={},
            )

        with open(sudo_file, "r") as f:
            sudo_password = f.read().strip()

    if payload.password:
        sudo_password = payload.password

    return ResultPayload(success=True, message=[], error=[], data=sudo_password)


def _load_role_eps(role_names: list[str]) -> ResultPayload:
    """
    Loads role plugins using the importlib metadata entry points, specifically looking for plugins under "chaos.roles"

    parameters:
        - role_names: a list of role names that need to be loaded. The function will attempt to load plugins that match these names.
    returns:
        - A ResultPayload indicating the success or failure of the role loading process, with any error messages in the error field,
            and a dictionary of loaded Role classes keyed by their names in the data field if successful. The function will look for
            plugins that match the specified role names, and if found, will load them and include them in the returned dictionary.
            If any role name is not found or if there are multiple plugins with the same name, it will return an error message
            indicating the issue.

    """

    from chaos.lib.utils import get_roleEps

    role_eps = get_roleEps()
    loaded_roles = {}

    ep_map = {}
    for ep in role_eps:
        if ep.name in ep_map:
            return ResultPayload(
                success=False,
                message=[],
                error=[
                    f"Multiple role plugins found with the name '{ep.name}'. Please resolve this conflict."
                ],
                data={},
            )
        ep_map[ep.name] = ep

    for role_name in role_names:
        if role_name not in ep_map:
            return ResultPayload(
                success=False,
                message=[],
                error=[f"No plugin found for role '{role_name}'."],
                data={},
            )
        try:
            loaded_role = ep_map[role_name].load()
            loaded_roles[role_name] = loaded_role
        except ImportError as e:
            return ResultPayload(
                success=False,
                message=[],
                error=[f"Error loading plugin for role '{role_name}': {str(e)}"],
                data={},
            )

    return ResultPayload(success=True, message=[], error=[], data=loaded_roles)
