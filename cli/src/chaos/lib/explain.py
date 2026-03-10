from importlib import import_module

from .args.dataclasses import ExplainPayload, ResultPayload


def _setup_method_explain(EXPLAIN_DISPATCHER, role):
    try:
        module_name, class_name = EXPLAIN_DISPATCHER[role].split(":")
        module = import_module(module_name)
        ExplainClass = getattr(module, class_name)
        ExplainObj = ExplainClass()
        return ExplainObj, None
    except (ImportError, AttributeError, ValueError) as e:
        return None, f"Could not load explanation class for role '{role}': {e}"


def _get_explain_subtopics(ExplainObj, role):
    manualOrder = getattr(ExplainObj, "_order", [])
    if manualOrder:
        return manualOrder

    available_methods = [
        m.replace("explain_", "")
        for m in dir(ExplainObj)
        if m.startswith("explain_") and m != "explain_"
    ]
    return sorted(list(set(available_methods) - {role}))


def handleExplain(payload: ExplainPayload, EXPLAIN_DISPATCHER) -> ResultPayload:
    topics = payload.topics
    complexity = payload.complexity
    if not isinstance(topics, list):
        topics = [topics]

    result_data = {}
    errors = []

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
