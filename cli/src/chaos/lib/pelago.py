from __future__ import annotations

from typing import TYPE_CHECKING

from pulumi import automation as auto

from chaos.lib.args.dataclasses import (
    DataGatherPayload,
    DataGatherRequest,
    PelagoPayload,
    ResultPayload,
)

if TYPE_CHECKING:
    from typing import Any, Callable

    from pulumi.automation import Stack

    from chaos.lib.isles.isle import Isle


def gather_provision(
    payload: PelagoPayload,
) -> tuple[DataGatherRequest | None, ResultPayload[dict[str, Any]]]:
    """
    Gathers necessary information for provisioning a Pulumi stack based on the provided payload.

    Args:
        payload (PelagoPayload): The initial payload containing stack configuration.

    Returns:
        DataGatherRequest: A request object containing the gathered information to be requested for provisioning.
        ResultPayload[dict[str, type[Isle]]]: A result payload containing the discovered Isles or error information.
    """
    request = DataGatherRequest("pelago_provision", [])

    all_isles_result = _discover_pelago_isles(payload.pelago)
    if not all_isles_result.success:
        return None, ResultPayload(
            success=False,
            message=[],
            error=all_isles_result.error,
            data=None,
        )

    if not all_isles_result.data:
        return None, ResultPayload(
            success=False,
            message=[],
            error=["No Isles discovered."],
            data=None,
        )

    needed_secrets = set()
    secret_needing_isles = set()
    for Isle in all_isles_result.data.values():
        secrets_needed = getattr(Isle, "secrets_needed", [])
        if secrets_needed:
            needed_secrets.update(secrets_needed)
            secret_needing_isles.add(Isle)

    joined_needed_secrets = "\n  -".join(needed_secrets)
    joined_secret_needing_programs = "\n  -".join(
        getattr(isle, "isle_name", isle.__name__) for isle in secret_needing_isles
    )
    if not payload.secrets:
        request.fields.append(
            DataGatherPayload(
                prompt=f"The following Pelago programs: {joined_secret_needing_programs} require the following secrets: {joined_needed_secrets}. None were provided. Do you wish to use them?",
                input_type="boolean",
                name="provide_secrets",
                default=False,
            )
        )

    return request, ResultPayload(
        success=True,
        message=[],
        error=[],
        data={
            "isle_classes": all_isles_result.data,
            "needed_secrets": needed_secrets,
        },
    )


def setup_pulumi(payload: PelagoPayload) -> ResultPayload[Stack]:
    """
    Sets up a Pulumi stack based on the provided payload.

    Args:
        payload (PelagoPayload): The payload containing stack configuration.

    Returns:
        ResultPayload[Stack]: A result payload containing the created stack or error information.
    """
    import os
    from pathlib import Path

    provided_secrets = payload.provided_secrets
    split_secrets = _split_secrets(payload)

    pulumi_backend_url = os.getenv(
        "PULUMI_BACKEND_URL",
        f"file://{os.getenv('PULUMI_BACKEND_PATH', str(Path.home() / '.pulumi' / 'backend'))}",
    )

    path_pbu = Path(pulumi_backend_url.replace("file://", ""))

    path_pbu.mkdir(parents=True, exist_ok=True)

    opts = auto.LocalWorkspaceOptions(
        env_vars={
            "PULUMI_BACKEND_URL": pulumi_backend_url,
            "PULUMI_CONFIG_PASSPHRASE": os.environ.get("PULUMI_CONFIG_PASSPHRASE", ""),
        }
    )

    try:
        stack = auto.create_or_select_stack(
            stack_name=payload.stack_name,
            project_name=payload.project_name,
            program=payload.pulumi_program,
            opts=opts,
        )
        if split_secrets and provided_secrets:
            for key, value in split_secrets.items():
                stack.set_config(key, auto.ConfigValue(value=value, secret=True))
        return ResultPayload(
            success=True,
            message=[f"Stack {payload.stack_name} created or selected successfully."],
            error=[],
            data=stack,
        )

    except auto.CommandError as e:
        return ResultPayload(
            success=False,
            message=[],
            error=[f"Pulumi command error: {str(e)}"],
            data=None,
        )

    except Exception as e:
        return ResultPayload(
            success=False,
            message=[],
            error=[f"An error occurred: {str(e)}"],
            data=None,
        )


def teardown_pulumi(payload: PelagoPayload) -> ResultPayload[None]:
    """
    Cleans up a Pulumi stack by removing any secrets that were used during the setup phase.

    Args:
        payload (PelagoPayload): The payload containing stack configuration.

    Returns:
        ResultPayload[None]: A result payload indicating success or failure of the teardown operation.

    Note:
        This should be used inside of a try/finally block to ensure that the stack is properly cleaned up after use.
    """
    stack = payload.stack
    secrets_used = payload.secrets_used
    errors = []
    if stack is None:
        return ResultPayload(
            success=False,
            message=[],
            error=["No stack provided for teardown."],
            data=None,
        )

    if not secrets_used:
        return ResultPayload(
            success=True,
            message=[
                f"Stack {stack.name} did not use secrets, No need to tear down configs."
            ],
            error=[],
            data=None,
        )

    try:
        for key in secrets_used:
            try:
                stack.remove_config(key)
            except Exception as e:
                errors.append(f"Failed to remove secret '{key}': {str(e)}")

        if errors:
            return ResultPayload(
                success=False,
                message=[],
                error=errors,
                data=None,
            )
        return ResultPayload(
            success=True,
            message=[f"Secrets removed from stack {stack.name}."],
            error=[],
            data=None,
        )

    except auto.CommandError as e:
        return ResultPayload(
            success=False,
            message=[],
            error=[f"Pulumi command error: {str(e)}"],
            data=None,
        )

    except Exception as e:
        return ResultPayload(
            success=False,
            message=[],
            error=[f"An error occurred: {str(e)}"],
            data=None,
        )


def create_pelago_program(
    payload: PelagoPayload, loaded_isles: dict[str, type[Isle]]
) -> ResultPayload[Callable[[], None]]:
    """
    Creates a Pulumi program function that dynamically routes configurations to their
    respective Isle implementations based on the provided payload and loaded Isles.

    Args:
        payload (PelagoPayload): The payload containing stack configuration.
        loaded_isles (dict[str, type[Isle]]): A dictionary of loaded Isles keyed by their names.

    Returns:
        ResultPayload[Callable[[], None]]: A result payload containing the created Pulumi program
             function or error information.
    """

    def pelago_program():
        for i, entry in enumerate(payload.pelago):
            isle_type = entry.get("isle")

            if not isle_type or isle_type not in loaded_isles:
                continue

            IsleClass = loaded_isles[isle_type]
            isle_config = entry.get("config", {})

            resource_name = entry.get("name", f"{isle_type}-isle-{i}")

            isle_instance = IsleClass(
                name=resource_name,
                config=isle_config,
            )

    return ResultPayload(
        success=True,
        message=["Pelago program created successfully."],
        error=[],
        data=pelago_program,
    )


def pulumi_up(payload: PelagoPayload) -> ResultPayload[None]:
    """
    Executes the Pulumi program by calling `pulumi up` on the provided stack.
    Args:
        payload (PelagoPayload): The payload containing stack configuration.
    Returns:
        ResultPayload[None]: A result payload indicating success or failure of the operation.
    """
    stack = payload.stack
    if stack is None:
        return ResultPayload(
            success=False,
            message=[],
            error=["No stack provided for pulumi up."],
            data=None,
        )

    try:
        stack.up(on_output=lambda output: print(output))
        return ResultPayload(
            success=True,
            message=[f"Pulumi up executed successfully on stack {stack.name}."],
            error=[],
            data=None,
        )

    except auto.CommandError as e:
        return ResultPayload(
            success=False,
            message=[],
            error=[f"Pulumi command error: {str(e)}"],
            data=None,
        )

    except Exception as e:
        return ResultPayload(
            success=False,
            message=[],
            error=[f"An error occurred: {str(e)}"],
            data=None,
        )


def _split_secrets(payload: PelagoPayload) -> dict[str, Any]:
    """
    Helper function to extract and split secrets from the provided payload.
    Args:
        payload (PelagoPayload): The payload containing secrets information.
    """

    provided_secrets = payload.provided_secrets
    needed_secrets = list(payload.needed_secrets)
    if not provided_secrets:
        return {}

    split_secrets = {}
    for key, value in provided_secrets.items():
        if key in needed_secrets:
            split_secrets[key] = value
    return split_secrets


def _discover_pelago_isles(
    pelago: list[dict[str, Any]],
) -> ResultPayload[dict[str, type[Isle]]]:
    """
    Discovers Pelago programs lazily based on the provided configuration.

    Args:
        pelago (list[dict[str, Any]]): A list of dictionaries containing Pelago program configurations.

    Returns:
        dict[str, type[Isle]]: A list of discovered Isles.
    """
    from chaos.lib.utils import get_isleEps

    pelago_isles = set()
    for entry in pelago:
        isle = entry.get("isle", "")
        pelago_isles.add(isle)

    if "" in pelago_isles:
        return ResultPayload(
            success=False,
            message=[],
            error=[
                "One or more entries in the Pelago configuration are missing the 'isle' key."
            ],
            data=None,
        )

    if not pelago_isles:
        return ResultPayload(
            success=False,
            message=[],
            error=["No isles specified in the Ch-obolo."],
            data=None,
        )

    isles_in_system = get_isleEps()

    loaded_isles: dict[str, type[Isle]] = {}

    ep_map = {}
    for ep in isles_in_system:
        if ep.name in ep_map:
            return ResultPayload(
                success=False,
                message=[],
                error=[
                    f"Multiple Isle plugins found with the name '{ep.name}'. Please resolve this conflict."
                ],
                data=None,
            )

        ep_map[ep.name] = ep

    for isle in pelago_isles:
        if isle not in ep_map:
            return ResultPayload(
                success=False,
                message=[],
                error=[
                    f"Pelago program specified for isle '{isle}' but no matching plugin found."
                ],
                data=None,
            )

        try:
            loaded_isle = ep_map[isle].load()
            loaded_isles[isle] = loaded_isle
        except ImportError as e:
            return ResultPayload(
                success=False,
                message=[],
                error=[f"Error loading plugin for isle '{isle}': {str(e)}"],
                data=None,
            )
    return ResultPayload(success=True, message=[], error=[], data=loaded_isles)
