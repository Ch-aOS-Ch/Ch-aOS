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
    from typing import Any

    from pulumi.automation import Stack

    from chaos.lib.isles.isle import Isle


def gather_provision(
    payload: PelagoPayload,
) -> tuple[DataGatherRequest | None, ResultPayload[set[type[Isle]]]]:
    """
    Gathers necessary information for provisioning a Pulumi stack based on the provided payload.

    Args:
        payload (PelagoPayload): The initial payload containing stack configuration.

    Returns:
        DataGatherRequest: A request object containing the gathered information to be requested for provisioning.
    """
    request = DataGatherRequest("pelago_provision", [])

    all_isles_result = _discover_pelago_programs(payload.pelago)
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
    for Isle in all_isles_result.data:
        secrets_needed = getattr(Isle, "secrets_needed", [])
        if secrets_needed:
            needed_secrets.update(secrets_needed)
            secret_needing_isles.add(Isle)

    joined_needed_secrets = "\n  -".join(needed_secrets)
    joined_secret_needing_programs = "\n  -".join(
        getattr(isle, "isle_name") for isle in secret_needing_isles
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
        success=True, message=[], error=[], data=all_isles_result.data
    )


def setup_pulumi(payload: PelagoPayload) -> ResultPayload[Stack]:
    """
    Sets up a Pulumi stack based on the provided payload.

    Args:
        payload (PelagoPayload): The payload containing stack configuration.

    Returns:
        ResultPayload[Stack]: A result payload containing the created stack or error information.
    """
    provided_secrets = payload.provided_secrets
    try:
        stack = auto.create_or_select_stack(
            stack_name=payload.stack_name,
            project_name=payload.project_name,
            program=payload.pulumi_program,
        )
        if provided_secrets:
            for key, value in provided_secrets.items():
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


def _discover_pelago_programs(
    pelago: list[dict[str, Any]],
) -> ResultPayload[set[type[Isle]]]:
    """
    Discovers Pelago programs lazily based on the provided configuration.

    Args:
        pelago (list[dict[str, Any]]): A list of dictionaries containing Pelago program configurations.

    Returns:
        set[type[Isle]]: A list of discovered Isles.
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
    loaded_isles = set()

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
            loaded_isles.add(loaded_isle)
        except ImportError as e:
            return ResultPayload(
                success=False,
                message=[],
                error=[f"Error loading plugin for isle '{isle}': {str(e)}"],
                data=None,
            )
    return ResultPayload(success=True, message=[], error=[], data=loaded_isles)
