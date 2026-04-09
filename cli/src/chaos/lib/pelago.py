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
    from importlib.metadata import EntryPoint

    from pulumi.automation import Stack


def gather_provision(
    payload: PelagoPayload,
) -> tuple[DataGatherRequest | None, ResultPayload[set[EntryPoint]]]:
    """
    Gathers necessary information for provisioning a Pulumi stack based on the provided payload.
    Args:
        payload (PelagoPayload): The initial payload containing stack configuration.
    Returns:
        DataGatherRequest: A request object containing the gathered information to be requested for provisioning.
    """
    request = DataGatherRequest("pelago_provision", [])

    all_programs_result = _discover_pelago_programs(payload.pelago)
    if not all_programs_result.success:
        return None, ResultPayload(
            success=False,
            message=[],
            error=all_programs_result.error,
            data=None,
        )

    if not all_programs_result.data:
        return None, ResultPayload(
            success=False,
            message=[],
            error=["No Pelago programs discovered."],
            data=None,
        )

    needed_secrets = set()
    secret_needing_programs = set()
    for program in all_programs_result.data:
        PelagoClass = program.load()
        secrets_needed = getattr(PelagoClass, "secrets_needed", [])
        if secrets_needed:
            needed_secrets.update(secrets_needed)
            secret_needing_programs.add(program)

    joined_needed_secrets = "\n  -".join(needed_secrets)
    joined_secret_needing_programs = "\n  -".join(
        program.name for program in secret_needing_programs
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
        success=True, message=[], error=[], data=all_programs_result.data
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
    pelago: list[dict[str, str]],
) -> ResultPayload[set[EntryPoint]]:
    """
    Discovers Pelago programs lazily based on the provided configuration.
    Args:
        pelago (list[dict[str, str]]): A list of dictionaries containing Pelago program configurations.
    Returns:
        set[EntryPoint]: A list of discovered Pelago program entry points.
    """
    from chaos.lib.plugDiscovery import get_plugins

    pelago_isles = set()
    for entry in pelago:
        isle = entry.get("isle", "")
        pelago_isles.add(isle)

    if not pelago_isles:
        return ResultPayload(
            success=False,
            message=[],
            error=["No isles specified in the Ch-obolo."],
            data=None,
        )

    isles_in_system = get_plugins()[7]
    if not isles_in_system:
        return ResultPayload(
            success=False,
            message=[],
            error=["No isles found in the system."],
            data=None,
        )

    discovered_programs = set()
    try:
        for isle in pelago_isles:
            if isle not in isles_in_system:
                return ResultPayload(
                    success=False,
                    message=[],
                    error=[
                        f"Isle '{isle}' specified in the Ch-obolo is not found in the system."
                    ],
                    data=None,
                )

            discovered_programs.add(isles_in_system[isle])

        return ResultPayload(
            success=True,
            message=[f"Discovered {len(discovered_programs)} Pelago programs."],
            error=[],
            data=discovered_programs,
        )

    except Exception as e:
        return ResultPayload(
            success=False,
            message=[],
            error=[f"An error occurred while discovering Pelago programs: {str(e)}"],
            data=None,
        )
