"""Core orchestration logic for the apply command, handling data gathering, state computation, and execution."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Literal

from omegaconf import DictConfig, ListConfig

from chaos.lib.args.dataclasses import (
    ApplyPayload,
    DataGatherPayload,
    DataGatherRequest,
    Delta,
    ResultPayload,
)
from chaos.lib.roles.role import Role

if TYPE_CHECKING:
    from pyinfra.api.host import Host
    from pyinfra.api.state import State


def gather_apply(
    payload: ApplyPayload,
) -> tuple[DataGatherRequest | None, ResultPayload[dict[str, Any] | None]]:
    """Gather necessary data for applying roles, such as sudo password and secrets if needed.

    Args:
        payload: the ApplyPayload containing the initial data and flags for the apply operation.

    Returns:
        - A DataGatherRequest if additional data needs to be gathered from the user, or None
        - A ResultPayload indicating the success or failure of the data gathering process, or None if a DataGatherRequest is returned.
            The ResultPayload.data["loaded_roles"] field will contain the loaded role classes based on the tags in the payload.
    """

    sudo_password_result = _handle_password(payload)
    if not sudo_password_result.success:
        return None, ResultPayload(
            success=False,
            message=[],
            error=[f"Error handling sudo password: {sudo_password_result.error}"],
            data=None,
        )

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
        if not result.data:
            result.data = {}
        result.data["sudo_password"] = sudo_password

    result_load = _load_role_eps(payload.tags)
    if not result_load.success:
        return request, result_load

    loaded_roles = result_load.data
    if not loaded_roles:
        result.success = False
        result.error.append("No valid roles found for the specified tags.")
        return request, result

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

    global_config = payload.global_config

    if not result.data:
        result.data = {}

    result.data["loaded_roles"] = loaded_roles
    result.data["global_config"] = global_config
    result.data["any_role_needs_secrets"] = bool(roles_that_need_secrets)
    if not request.fields:
        return None, result
    return request, result


def gather_fleet(
    payload: ApplyPayload, chobolo_config: DictConfig | ListConfig, chobolo_path: str
) -> tuple[DataGatherRequest | None, ResultPayload[dict[str, Any]]]:
    """Gather necessary data for fleet configuration, such as host information and parallelism settings.

    Args:
        payload: the ApplyPayload containing the initial data and flags for the apply operation.
        chobolo_config: the loaded chobolo configuration as a DictConfig object.
        chobolo_path: the file path to the chobolo configuration file, used for error messages.

    Returns:
        - A DataGatherRequest if additional data needs to be gathered from the user, or None
        - A ResultPayload indicating the success or failure of the data gathering process.

    Notes:
        Expected format in chobolo file:
        ```yaml
        fleet:
            parallelism: int (optional, default 0 for no parallelism)
            hosts:
                host1:
                    param1: value1
                    param2: value2

            # OPTIONAL
            boats:
                - provider: boat_provider_name
                  config:
                      param1: value1
                      param2: value2

            # OPTIONAL
            restrictions:
                black_list:
                    host1:
                        role1: true
                        role2: true
                        # host1 wont be able to run role1 nor role2
                    host2:
                        role3: true
                        # host2 wont be able ot run role3
                allow_list:
                    host1:
                        role3: true
                        # host1 will ONLY be able to run role3
                    host3:
                        role1: true
                        role4: true
                        # host3 will ONLY be able to run role
        ```
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

        boat_config = boat_config.get("fleet", {}) if boat_config else fleet_config
    except Exception as e:
        return None, ResultPayload(success=False, error=[str(e)])

    fleet_hosts = boat_config.get("hosts", {})

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
    container = cast(dict[str, dict[str, Any]], container)

    if not isinstance(container, dict):
        return None, ResultPayload(
            success=False,
            error=[
                f"Fleet hosts configuration in {chobolo_path} is malformed. Expected a dict of hosts"
            ],
        )

    messages = []
    for hostname, host_data in container.items():
        if not isinstance(host_data, dict):
            messages.append(
                f"Malformed host data for host '{hostname}' in fleet configuration {host_data}. It must be a dictionary of host parameters. Skipping."
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


def run_context(
    payload: ApplyPayload,
    role: Role,
    host: Host,
    chobolo_data: dict[str, Any],
) -> ResultPayload[dict[str, Any]]:
    """Run the context method for a given role and host, gathering necessary configuration and secrets.

    Args:
        payload: the ApplyPayload containing the initial data and flags for the apply operation.
        role: the Role class for which to run the context method.
        host: the Host object representing the target host for which to gather context.

    Returns:
        - A ResultPayload indicating the success or failure of the context gathering process, with the gathered context data if successful.
            The context data is inside of the ResultPayload.data field, and any error messages are in the error field.
    """

    if role.needs_secrets and not payload.secrets:
        return ResultPayload(
            success=False,
            message=[],
            error=[f"Role '{role.name}' requires secrets but none were provided."],
            data={},
        )

    chobolo_for_role = chobolo_data

    secrets_for_role = {}
    secrets_result = None

    if role.needs_secrets:
        secrets_result = _handle_secrets_for_role(role, payload)

        if not secrets_result.success:
            return ResultPayload(
                success=False,
                message=[],
                error=[
                    f"Role '{role.name}' requires secrets but they could not be loaded: {secrets_result.error}"
                ],
                data={},
            )

        if not secrets_result.data:
            return ResultPayload(
                success=False,
                message=[],
                error=[
                    f"Role '{role.name}' requires secrets but no secrets were provided."
                ],
                data={},
            )

        secrets_for_role = secrets_result.data

    if payload.pyinfra_state is None:
        return ResultPayload(
            success=False,
            message=[],
            data={},
            error=["payload.pyinfra_state is not a State instance."],
        )
    context = role.get_context(
        payload.pyinfra_state, host, chobolo_for_role, secrets_for_role
    )

    return ResultPayload(success=True, message=[], error=[], data=context)


def run_delta(
    context: dict[str, Any], role: Role, role_name: str
) -> ResultPayload[Delta]:
    """Run the delta method for a given role and context, computing the necessary changes to apply the role.

    Args:
        context: the context data gathered for the role, which should contain all necessary information for computing the delta.
            this should be the data returned in the ResultPayload.data field from the run_context function.
        role: the Role class for which to run the delta method.
        role_name: the name of the role, used for error messages.

    Returns:
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
            data=None,
        )
    return ResultPayload(success=True, message=[], error=[], data=delta)


def run_plan(
    payload: ApplyPayload,
    delta: Delta,
    role: Role,
    role_name: str,
    host: Host,
) -> ResultPayload[dict[str, Any]]:
    """Runs the plan method for a given role and host, computing the necessary
        operations to apply the role, while also checking against any allowlist or blacklist restrictions for the role and host.

    Args:
        payload: the ApplyPayload containing the initial data and flags for the apply operation.
        delta: the Delta object representing the changes that need to be applied for the role, which should be the output from
            the run_delta function. this should be the data returned in the ResultPayload.data field from the run_delta function.
        role: the Role class for which to run the plan method.
        role_name: the name of the role, used for error messages and checking restrictions.
        host: the Host object representing the target host for which to compute the plan.

    Returns:
        - A ResultPayload indicating the success or failure of the plan computation process, with any error
            messages in the error field, and the computed plan in the data field if successful.
            The plan should be the data returned from the role.plan() method if all checks pass and the plan is computed successfully.
            If there are any errors or if the role is skipped due to restrictions, the plan will not be included in the data field.
    """

    if payload.pyinfra_state is None:
        return ResultPayload(
            success=False,
            message=[],
            error=["payload.pyinfra_state is not a State instance."],
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


def execute_plans(payload: ApplyPayload) -> ResultPayload[dict[str, Any] | None]:
    """Executes all computed state operations for the roles on the target hosts using pyinfra, and gathers the results of the execution.

    Args:
        payload: the ApplyPayload containing the pyinfra state with the computed plans for each role and host
            as well as any flags for telemetry.
    """

    from pyinfra.api.operations import run_ops

    try:
        if payload.dry:
            return ResultPayload(success=True, message=[], error=[])

        if payload.pyinfra_state:
            run_ops(payload.pyinfra_state, payload.serial, payload.no_wait)
        return ResultPayload(success=True, message=[], error=[])
    except Exception as e:
        return ResultPayload(
            success=False,
            message=[],
            error=[f"Error executing plans with pyinfra: {str(e)}"],
            data={},
        )


def resolve_aliases(payload: ApplyPayload) -> ResultPayload[list[str]]:
    """Resolves any aliases in the payload tags based on the plugin aliases and user configuration aliases,
         while also checking for circular references and conflicts.

    Args:
        payload: the ApplyPayload containing the initial tags and global configuration for resolving aliases.

    Returns:
        - A ResultPayload indicating the success or failure of the alias resolution process, with any error messages in the error field,
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


def setup_pyinfra(payload: ApplyPayload) -> ResultPayload[Any | None]:
    """Set up the pyinfra state and inventory based on the gathered fleet configuration, and establish connections to the target hosts.

    Args:
        payload: the ApplyPayload containing the gathered data for the apply operation, including fleet configuration and sudo password.

    Returns:
        - ResultPayload indicating the success or failure of the pyinfra setup process, with any error messages in the error field.
            Additionally, if successful, the ResultPayload.data field will contain the initialized pyinfra State object that is ready
            for executing plans.
    """

    import logging
    import time

    from pyinfra.api.config import Config
    from pyinfra.api.connect import connect_all
    from pyinfra.api.state import State, StateStage
    from pyinfra.context import ctx_state

    from .telemetry import ChaosTelemetry

    try:
        inventory, _, parallels = _setup_hosts(payload)

        config = Config(
            PARALLEL=parallels,
            DIFF=payload.logbook,
        )

        state = State(inventory, config)
        state.current_stage = StateStage.Prepare

        start_time = time.time()

        if payload.logbook:
            limani_result = _resolve_limani(payload.global_config, payload)
            if not limani_result.success:
                return ResultPayload(
                    success=False,
                    message=[],
                    error=[
                        f"Error resolving limani for telemetry: {limani_result.error}"
                    ],
                    data=None,
                )

            if not limani_result.data:
                return ResultPayload(
                    success=False,
                    message=[],
                    error=["No limani specified for telemetry."],
                    data=None,
                )

            ChaosTelemetry.load_limani_plugin(limani_result.data, payload.global_config)

            state.add_callback_handler(ChaosTelemetry())
            pyinfra_logger = logging.getLogger("pyinfra")
            pyinfra_logger.setLevel(logging.DEBUG)
            handler = ChaosTelemetry.PyinfraFactLogHandler()
            pyinfra_logger.addHandler(handler)
            ChaosTelemetry.start_run()

        ctx_state.set(state)

        password = payload.password
        state.config.SU_PASSWORD = password
        state.config.SUDO_PASSWORD = password

        connect_all(state)

        end_time = time.time()
        setup_duration = end_time - start_time

        if payload.logbook:
            ChaosTelemetry.record_setup_phase(state, setup_duration)
            _collect_fleet_health(state, stage="pre_operations")

        return ResultPayload(success=True, message=[], error=[], data=state)
    except Exception as e:
        return ResultPayload(
            success=False,
            message=[],
            error=[f"Error setting up pyinfra: {str(e)}"],
            data=None,
        )


def teardown_pyinfra(
    payload: ApplyPayload, run_status: Literal["success", "failure"]
) -> ResultPayload[dict[str, Any]]:
    """Teardown the pyinfra state and connections after the apply operation is complete.

    Args:
        payload: the ApplyPayload containing the pyinfra state to be torn down.

    Returns:
        - ResultPayload indicating the success or failure of the pyinfra teardown process, with any error messages in the error field.

    Notes:
        Should be used inside of a finally block to ensure all connections will be properly closed.
    """

    from pyinfra.api.connect import disconnect_all

    try:
        if payload.logbook:
            from .telemetry import ChaosTelemetry

            if payload.export_logs:
                ChaosTelemetry.export_report()
            if payload.pyinfra_state:
                _collect_fleet_health(payload.pyinfra_state, stage="post_operations")
            ChaosTelemetry.end_run(run_status)

        if payload.pyinfra_state:
            disconnect_all(payload.pyinfra_state)
        return ResultPayload(success=True, message=[], error=[], data={})
    except Exception as e:
        return ResultPayload(
            success=False,
            message=[],
            error=[f"Error tearing down pyinfra: {str(e)}"],
            data={},
        )


def resolve_allowlist_blacklist(
    restrictions: dict[str, dict[str, dict[str, bool]]],
    role_name: str,
    host: Host,
) -> ResultPayload[dict[str, Any]] | None:
    """This function resolves all blacklist and allowlist restrictions given for a role and host, and determines if the role should be ran
        in said host or if there are any conflicts in the configuration that should be reported as errors.

    Args:
        role_name: the name of the role for which to check restrictions, used for error messages.
        host: the Host object representing the target host for which to check restrictions, used for error messages.
        restrictions: a dictionary containing any allowlist or blacklist restrictions for roles and hosts, used
            to determine if the role should be applied to the host or if there are any conflicts in the configuration.

    Returns:
        ResultPayload[dict[str, Any]] | None: A ResultPayload indicating the success or failure of the resolution process.

    Notes:
        It should be called before running the get_context for a role on a host.

        This dictionary should be inside of the chobolo file, and should have the following structure:
        ```yaml
            fleet:
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
        ```

        The function will check the restrictions in the following order:
            1. A conflict check to see if the role is both blacklisted and allowlisted for the host, which will result in an error.
            2. A check to see if the role is blacklisted for the host, which will skip the role for that host.
            3. A check to see if the host is completely blacklisted (if it is host: {} and not in an allow_list), which will skip all roles
                for that host.
            4. A check to see if the host is allowlisted but the role is not on the allowlist, which will skip it.
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


def run_filtered_context(
    host: Host,
    roles: list[Role],
    payload: ApplyPayload,
    chobolo_config: dict[str, Any],
    restrictions: dict[str, dict[str, dict[str, bool]]],
) -> ResultPayload[dict[str, Any]]:
    """
    run_context implementation integrated with resolve_allowlist_blacklist to filter out roles that should not be applied to the host
        based on the restrictions specified in the chobolo configuration.

    Args:
        host (Host): The Host object representing the target host for which to gather context.
        roles (list[Role]): A list of Role classes that are applicable to the host based on the fleet configuration.
        payload (ApplyPayload): The ApplyPayload containing the initial data and flags for the apply operation.
        chobolo_config (dict[str, Any]): The entire chobolo configuration data, used for passing to the context method of the roles.
        restrictions (dict[str, dict[str, dict[str, bool]]]): A dictionary containing any allowlist or blacklist restrictions for
            roles and hosts, used to determine if each role should be applied to the host or if there are any conflicts in the configuration.

    Returns:
        ResultPayload[dict[str, Any]]: A ResultPayload indicating the success or failure of the context gathering process for the host,
            with the gathered context data for all applicable roles in the data field if successful, and any error messages in the
            error field.


    Notes:
        It should be called before running the get_context for a role on a host.

        This dictionary should be inside of the chobolo file, and should have the following structure:
    ```yaml
        fleet:
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
    ```
    """

    host_data = {"host": host, "roles": {}}
    result = ResultPayload(success=True, message=[], error=[])
    for role in roles:
        allowlist_blacklist_result = resolve_allowlist_blacklist(
            restrictions, role.name, host
        )
        if allowlist_blacklist_result and not allowlist_blacklist_result.success:
            result.error = allowlist_blacklist_result.error
            result.success = False
            break
        elif (
            allowlist_blacklist_result
            and allowlist_blacklist_result.success
            and allowlist_blacklist_result.message
        ):
            continue

        context_result = run_context(payload, role, host, chobolo_config)
        if not context_result.success:
            result.error.extend(context_result.error)
            continue

        if context_result.data is None:
            result.error.append(
                f"Context for role '{role.name}' on host '{host.name}' returned None."
            )
            continue

        host_data["roles"][role.name] = {
            "role": role,
            "context": context_result.data,
        }
    result.data = host_data
    return result


def get_configs(
    payload: ApplyPayload,
) -> tuple[DictConfig, ResultPayload[dict[str, Any]]]:
    """Loads global configuration from a chobolo file and validates paths for chobolo,
         secrets file, and sops file based on the payload and global configuration.

    Args:
        payload: the ApplyPayload containing any overrides for configuration paths,
             such as chobolo file path, secrets file path, and sops file path.

    Returns:
        - A DictConfig object representing the loaded global configuration, which may include overrides from the payload.
        - A ResultPayload indicating the success or failure of the configuration loading and validation process, with
            any error messages in the error field, and the relevant configuration data (such as validated paths) in
            the data field if successful.
    """

    import os
    from pathlib import Path
    from typing import cast

    from omegaconf import OmegaConf

    from .utils import validate_path

    CONFIG_DIR = os.getenv("CHAOS_CONFIG_DIR", Path.home() / ".config" / "chaos")
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


def _collect_fleet_health(
    state: State, stage: Literal["pre_operations", "post_operations"]
) -> None:
    """
    Asyncronously collects RAM and Load Average facts from all hosts in the fleet and records them in the telemetry system.

    if state.pool is available, it uses it to parallelize fact collection across hosts.
    Otherwise, it falls back to sequential collection.
    Args:
        state (State): The current pyinfra state containing the inventory and connection pool.
        stage (str): The stage of the operation (e.g., "pre_operations", "post_operations") for telemetry recording.
    """
    from .facts.facts import LoadAverage, RamUsage
    from .telemetry import ChaosTelemetry

    def _fetch_and_record(host):
        ram_data = host.get_fact(RamUsage)
        load_data = host.get_fact(LoadAverage)
        ChaosTelemetry.record_snapshot(host, ram_data, load_data, stage=stage)

    if state.pool:
        state.pool.map(_fetch_and_record, state.inventory.iter_activated_hosts())
    else:
        for host in state.inventory.iter_activated_hosts():
            _fetch_and_record(host)


def _resolve_limani(
    global_config: dict[str, Any], payload: ApplyPayload
) -> ResultPayload[str]:
    if payload.limani:
        limani_name = payload.limani
    else:
        limani_name = global_config.get("limani", "")

    if not limani_name:
        return ResultPayload(
            success=False,
            message=[],
            error=["No limani specified in payload or global config."],
            data=None,
        )

    return ResultPayload(success=True, message=[], error=[], data=limani_name)


def _load_boats(necessary_boats: set[str]) -> ResultPayload[list[Any]]:
    """Loads boat plugins using the importlib metadata entry points, specifically looking for plugins under "chaos.boats"
        It attempts to load all boat plugins and returns a list of the loaded boat classes.

    Args:
        necessary_boats: a set of boat provider names that are needed for the fleet configuration.
             Only boats with providers in this set will be loaded.

    Returns:
        - A ResultPayload indicating the success or failure of the boat loading process,
            with any error messages in the error field, and a list of loaded boat classes in the data field if successful.

    Notes:
        This function is lazy and only loads boats that are necessary.
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
) -> tuple[DictConfig, ResultPayload[list[Any] | None]]:
    """Handles the processing of boats for fleet configuration, including loading necessary boat plugins and invoking their
         get_fleet methods to gather host information.

    Args:
        global_state: the current global state as a DictConfig, which may be mutated by the boats' get_fleet methods to
             include fleet information.
             This state must be the chobolo file.
        boats: a ListConfig containing the boat configurations from the chobolo file, where each boat configuration should
            include a "provider" key indicating the boat provider, and an optional "config" key with configuration for that boat.

    Returns:
        - A DictConfig representing the potentially mutated global state after processing the boats.
        - A ResultPayload indicating the success or failure of the boat processing, with any error messages in the error field.

    Notes:
        mutates:
            - global_state: this may be mutated by the boats' get_fleet methods to include new hosts and information to the
                global state that will be used for setting up the fleet and inventory.

        expected format for boats in chobolo file:
        ```yaml
        fleet:
            boats:
                - provider: boat_provider_name
                  config:
                    param1: value1
                    param2: value2
        ```
    """

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

    boat_map = {boat_class.name: boat_class for boat_class in loaded_boat_classes}

    for boat_config in boats:
        provider = boat_config.get("provider")
        if provider and provider in boat_map:
            boat_class = boat_map[provider]
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
    """Sets up the inventory of hosts for pyinfra based on the fleet configuration gathered from the chobolo file,
         and determines the parallelism settings for executing plans on the fleet.

    Args:
        payload: the ApplyPayload containing the gathered data for the apply operation, including fleet configuration
            such as the list of target hosts and parallelism settings.

    Returns:
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


def _handle_secrets_for_role(
    role: Role,
    payload: ApplyPayload,
    role_name: str = "",
) -> ResultPayload[dict[str, Any]]:
    """Handles the loading and decryption of secrets for a given role based on the payload and global configuration.

    Args:
        role: the Role class for which to handle secrets, used to determine if secrets are needed and what keys are necessary.
        payload: the ApplyPayload containing any overrides for secrets file path and sops file path, as well as the secrets context.
            This payload must contain the decrypted secrets in the payload.decrypted_secrets attribute, which should be a string
            representation of the decrypted secrets data.
        role_name: the name of the role, used for error messages.

    Returns:
        - A ResultPayload indicating the success or failure of the secrets handling process, with any error messages in the error field,
            and a dictionary of secrets for the role in the data field if successful. The secrets for the role will be filtered based on
            the necessary_secret_dict_keys specified by the role, and will only include those keys that are present in the loaded secrets.
    """

    decrypted_secrets = payload.decrypted_secrets

    if role.needs_secrets and payload.secrets:
        if not decrypted_secrets:
            return ResultPayload(
                success=False,
                message=[],
                error=["No secrets could be decrypted."],
                data={},
            )

        secrets_for_role = {}
        for key in role.necessary_secret_dict_keys:
            if key == ".":
                secrets_for_role["."] = decrypted_secrets
                continue

            keys_path = key.split(".")
            value = decrypted_secrets
            try:
                for k in keys_path:
                    value = value[k]
            except (KeyError, TypeError):
                value = None

            if value is None:
                return ResultPayload(
                    success=False,
                    message=[],
                    error=[
                        f"Role '{role_name}' requires secret key '{key}' which was not found in the decrypted secrets."
                    ],
                    data={},
                )

            secrets_for_role[key] = value

        return ResultPayload(success=True, message=[], error=[], data=secrets_for_role)
    return ResultPayload(success=True, message=[], error=[], data={})


def _handle_password(payload: ApplyPayload) -> ResultPayload[str | None]:
    """Handles the retrieval of the sudo password based on the payload, either from a specified file or directly from the payload.

    Args:
        payload: the ApplyPayload containing any overrides for the sudo password file path or the password itself.

    Returns:
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
                data=None,
            )

        sudo_file = Path(payload.sudo_password_file)
        if not sudo_file.exists():
            return ResultPayload(
                success=False,
                message=[],
                error=[f"Sudo password file not found: {sudo_file}"],
                data=None,
            )

        if not sudo_file.is_file():
            return ResultPayload(
                success=False,
                message=[],
                error=[f"Sudo password file path is not a file: {sudo_file}"],
                data=None,
            )

        with open(sudo_file, "r") as f:
            sudo_password = f.read().strip()

    if payload.password:
        sudo_password = payload.password

    return ResultPayload(success=True, message=[], error=[], data=sudo_password)


def _load_role_eps(role_names: list[str]) -> ResultPayload[dict[str, Any]]:
    """Loads role plugins using the importlib metadata entry points, specifically looking for plugins under "chaos.roles"

    Args:
        role_names: a list of role names that need to be loaded. The function will attempt to load plugins that match these names.

    Returns:
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
            loaded_roles[role_name] = loaded_role()
        except ImportError as e:
            return ResultPayload(
                success=False,
                message=[],
                error=[f"Error loading plugin for role '{role_name}': {str(e)}"],
                data={},
            )

    return ResultPayload(success=True, message=[], error=[], data=loaded_roles)
