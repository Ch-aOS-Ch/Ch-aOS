from __future__ import annotations

from importlib import import_module
from typing import TYPE_CHECKING

from .args.dataclasses import ExplainPayload, ResultPayload

if TYPE_CHECKING:
    from typing import Any, TypedDict

    class ExplainContentResult(TypedDict):
        type: str
        role: str
        sub_topic: str | None
        content: str | list[str]

    class ExplainListResult(TypedDict):
        type: str
        role: str
        sub_topics: list[str]

    ExplainResult = ExplainContentResult | ExplainListResult


def _setup_method_explain(EXPLAIN_DISPATCHER, role) -> tuple[Any, str | None]:
    """Sets up and initializes the explanation class for a given role.

    Args:
        EXPLAIN_DISPATCHER (dict): A dictionary mapping roles to their explanation module and class names (e.g. "module:class").
        role (str): The name of the role for which to instantiate the explanation object.

    Returns:
        tuple[Any, str | None]: A tuple containing the initialized explanation object on success and an error message on failure.
    """
    try:
        module_name, class_name = EXPLAIN_DISPATCHER[role].split(":")
        module = import_module(module_name)
        ExplainClass = getattr(module, class_name)
        ExplainObj = ExplainClass()
        return ExplainObj, None
    except (ImportError, AttributeError, ValueError) as e:
        return None, f"Could not load explanation class for role '{role}': {e}"


def _get_explain_subtopics(ExplainObj, role) -> list[str]:
    """Retrieves the available subtopics for an initialized explanation object.

    Args:
        ExplainObj (Any): The instantiated explanation object for a role.
        role (str): The role name, used to exclude the base role name from the subtopics list.

    Returns:
        list[str]: A sorted list of available subtopics, retrieved either from a manual `_order` attribute or by inspecting methods prefixed with `explain_`.
    """
    manualOrder = getattr(ExplainObj, "_order", [])
    if manualOrder:
        return manualOrder

    available_methods = [
        m.replace("explain_", "")
        for m in dir(ExplainObj)
        if m.startswith("explain_") and m != "explain_"
    ]
    return sorted(list(set(available_methods) - {role}))


def handleExplain(
    payload: ExplainPayload, EXPLAIN_DISPATCHER: dict[str, str]
) -> ResultPayload[dict[str, ExplainResult]]:
    """Handles the resolution and fetching of explanations for provided topics.

    Args:
        payload (ExplainPayload): The payload containing the requested topics and desired complexity level.
        EXPLAIN_DISPATCHER (dict): A mapping of available roles to their specific explanation modules.

    Returns:
        ResultPayload[]: The result payload containing a dictionary of fetched explanations or list of subtopics on success, and any errors encountered during resolution.

    Notes:
        Topics should be passed as either "role" or "role.sub_topic". If "role.list" is requested, it will list all available subtopics for that role.
    """
    topics = payload.topics
    complexity = payload.complexity
    if not isinstance(topics, list):
        topics = [topics]

    result_data: dict[str, ExplainResult] = {}
    errors: list[str] = []

    for topic in topics:
        parts = topic.split(".")
        role = parts[0]
        sub_topic = parts[1] if len(parts) > 1 else None

        if role in EXPLAIN_DISPATCHER:
            ExplainObj, err = _setup_method_explain(EXPLAIN_DISPATCHER, role)
            if err:
                errors.append(err)
                continue

            methodName = f"explain_{sub_topic}" if sub_topic else f"explain_{role}"

            if sub_topic == "list":
                exp_list = _get_explain_subtopics(ExplainObj, role)
                result_data[topic] = {
                    "type": "list",
                    "role": role,
                    "sub_topics": exp_list,
                }
                continue

            if hasattr(ExplainObj, methodName):
                method = getattr(ExplainObj, methodName)
                explanation = method(complexity)
                result_data[topic] = {
                    "type": "explanation",
                    "role": role,
                    "sub_topic": sub_topic,
                    "content": explanation,
                }
            else:
                available_methods = _get_explain_subtopics(ExplainObj, role)
                errors.append(
                    f"No explanation found for sub-topic '{sub_topic}' in role '{role}'."
                )
                if available_methods:
                    errors.append(
                        f"Available sub-topics for '{role}': {available_methods}"
                    )
                else:
                    errors.append(
                        "Poorly configured explanation module. \n(if you're a dev, make sure your module has a class with functions that simply return a dict with your needed explanations.)"
                    )
        else:
            errors.append(f"No explanation found for topic '{topic}'.")

    success = len(errors) == 0
    return ResultPayload(success=success, data=result_data, error=errors)
