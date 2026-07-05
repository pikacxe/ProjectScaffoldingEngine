import os

import yaml
from textx.exceptions import TextXSemanticError, TextXSyntaxError


BASE_DIR = os.path.dirname(__file__)
HEURISTICS_DIR = os.path.join(BASE_DIR, "heuristics")
SUPPORTED_TARGETS = {"dotnet"}


class DslValidationError(ValueError):
    pass


def validate_model(model, source_text: str = None):
    errors = []

    errors.extend(validate_project(model))
    errors.extend(validate_contexts(model, source_text))
    errors.extend(validate_infrastructure(model))
    errors.extend(validate_capabilities(model))

    if errors:
        raise DslValidationError(format_validation_error(errors))


def validate_project(model):
    errors = []

    target = (getattr(model, "target", None) or "dotnet").lower()
    if target not in SUPPORTED_TARGETS:
        errors.append(f"Project target '{getattr(model, 'target', None)}' is not supported. Supported targets: dotnet.")

    archetype = getattr(getattr(model, "archetype", None), "value", None)
    supported_archetypes = load_supported_archetypes()
    normalized_archetype = normalize_name(archetype)

    if normalized_archetype and normalized_archetype not in supported_archetypes:
        errors.append(
            f"Archetype '{archetype}' is not recognized. Supported archetypes: {', '.join(sorted(supported_archetypes.values()))}."
        )

    return errors


def validate_contexts(model, source_text: str = None):
    errors = []
    context_names = []
    known_types = collect_known_types(model)

    for context in getattr(model, "contexts", []) or []:
        context_name = context.name
        normalized_context_name = normalize_name(context_name)
        context_location = location_from_node(context, source_text)

        if normalized_context_name in context_names:
            errors.append(
                format_problem(
                    f"Duplicate context name '{context_name}'. Context names must be unique.",
                    context_location,
                )
            )
        else:
            context_names.append(normalized_context_name)

        errors.extend(validate_named_collection(context_name, "entity", context.entities, source_text))
        errors.extend(validate_named_collection(context_name, "value object", context.valueObjects, source_text))
        errors.extend(validate_named_collection(context_name, "aggregate", context.aggregates, source_text))
        errors.extend(validate_aggregates(context_name, context.entities, context.aggregates, source_text))
        errors.extend(validate_property_types(context_name, context.entities, context.valueObjects, known_types, source_text))

    return errors


def validate_infrastructure(model):
    infra = getattr(model, "infrastructure", None)
    if not infra:
        return []

    errors = []

    for label in ("database", "cache", "broker"):
        item = getattr(infra, label, None)
        if item and not getattr(item, "type", None):
            errors.append(f"Infrastructure {label} must specify a type.")

    return errors


def validate_capabilities(model):
    capabilities = getattr(model, "capabilities", None)
    explicit = getattr(capabilities, "capabilities", []) or []
    if not explicit:
        return []

    registry = load_capability_registry()
    available = {normalize_name(name) for name in registry.keys()}
    errors = []

    for capability in explicit:
        name = normalize_name(capability.name)
        if name not in available:
            errors.append(
                f"Capability '{capability.name}' is not recognized. Available capabilities: {', '.join(sorted(registry.keys()))}."
            )

    return errors


def validate_named_collection(context_name, item_label, items, source_text: str = None):
    errors = []
    seen = set()

    for item in items or []:
        name = normalize_name(item.name)
        if name in seen:
            errors.append(
                format_problem(
                    f"Context '{context_name}' contains duplicate {item_label} name '{item.name}'.",
                    location_from_node(item, source_text),
                )
            )
        else:
            seen.add(name)

    return errors


def validate_aggregates(context_name, entities, aggregates, source_text: str = None):
    errors = []
    entity_names = {normalize_name(entity.name): entity.name for entity in entities or []}

    for aggregate in aggregates or []:
        aggregate_location = location_from_node(aggregate, source_text)
        root_entity = getattr(aggregate, "root", None)
        root_name = getattr(root_entity, "name", None)
        if not root_name:
            errors.append(
                format_problem(
                    f"Aggregate '{aggregate.name}' in context '{context_name}' must define a root entity.",
                    aggregate_location,
                )
            )
            continue

        if normalize_name(root_name) not in entity_names:
            errors.append(
                format_problem(
                    f"Aggregate '{aggregate.name}' in context '{context_name}' references unknown root '{root_name}'.",
                    aggregate_location,
                )
            )

        child_names = set()
        for child_entity in getattr(aggregate, "children", []) or []:
            child_name = getattr(child_entity, "name", None)
            normalized_child = normalize_name(child_name)
            if normalized_child in child_names:
                errors.append(
                    format_problem(
                        f"Aggregate '{aggregate.name}' in context '{context_name}' contains duplicate child '{child_name}'.",
                        aggregate_location,
                    )
                )
                continue

            child_names.add(normalized_child)

            if normalized_child not in entity_names:
                errors.append(
                    format_problem(
                        f"Aggregate '{aggregate.name}' in context '{context_name}' references unknown child '{child_name}'.",
                        aggregate_location,
                    )
                )

    return errors


def validate_property_types(context_name, entities, value_objects, known_types, source_text: str = None):
    errors = []

    local_types = {
        normalize_name(item.name): item.name
        for item in (entities or []) + (value_objects or [])
    }

    for entity in entities or []:
        errors.extend(
            validate_properties_for_item(context_name, "entity", entity.name, entity.properties, known_types, local_types, source_text)
        )

    for value_object in value_objects or []:
        errors.extend(
            validate_properties_for_item(context_name, "value object", value_object.name, value_object.properties, known_types, local_types, source_text)
        )

    return errors


def validate_properties_for_item(context_name, item_label, item_name, properties, known_types, local_types, source_text: str = None):
    errors = []

    for property_item in properties or []:
        property_name = property_item.name
        property_type = property_item.type
        normalized_type = normalize_name(property_type)
        if normalized_type not in known_types and normalized_type not in local_types:
            errors.append(
                format_problem(
                    f"{item_label.title()} '{item_name}' in context '{context_name}' uses unknown property type '{property_type}' for '{property_name}'.",
                    location_from_node(property_item, source_text),
                )
            )

    return errors


def collect_known_types(model):
    primitive_types = {
        "guid",
        "datetime",
        "string",
        "int",
        "long",
        "bool",
        "boolean",
        "decimal",
        "double",
        "float",
    }

    local_types = set()
    for context in getattr(model, "contexts", []) or []:
        for entity in context.entities:
            local_types.add(normalize_name(entity.name))
        for value_object in context.valueObjects:
            local_types.add(normalize_name(value_object.name))

    return primitive_types | local_types


def location_from_node(node, source_text: str = None):
    if not node:
        return None

    position = getattr(node, "_tx_position", None)
    if position is None or source_text is None:
        return None

    line = source_text.count("\n", 0, position) + 1
    last_newline = source_text.rfind("\n", 0, position)
    column = position + 1 if last_newline < 0 else position - last_newline
    return f"line {line}, col {column}"


def load_supported_archetypes():
    path = os.path.join(HEURISTICS_DIR, "archetypes.yaml")
    with open(path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}

    return {normalize_name(name): name for name in data.keys()}


def load_capability_registry():
    path = os.path.join(HEURISTICS_DIR, "capabilities.yaml")
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def normalize_name(value):
    return (value or "").replace("_", "").replace("-", "").lower()


def format_validation_error(errors):
    lines = ["DSL validation failed:"]
    lines.extend(f"- {error}" for error in errors)
    return "\n".join(lines)


def format_problem(message, location: str = None):
    if location:
        return f"{location}: {message}"

    return message


def format_user_error(error):
    if isinstance(error, DslValidationError):
        return str(error)

    if isinstance(error, TextXSyntaxError):
        location = format_exception_location(error)
        message = getattr(error, "message", None) or str(error)
        if location:
            return f"DSL syntax error at {location}: {message}"
        return f"DSL syntax error: {message}"

    if isinstance(error, TextXSemanticError):
        location = format_exception_location(error)
        message = getattr(error, "message", None) or str(error)
        if location:
            return f"DSL semantic error at {location}: {message}"
        return f"DSL semantic error: {message}"

    return str(error)


def format_exception_location(error):
    line = getattr(error, "line", None)
    column = getattr(error, "col", None)

    if line is None:
        return None

    if column is None:
        return f"line {line}"

    return f"line {line}, col {column}"