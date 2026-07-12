import os
from dataclasses import dataclass

import yaml
from textx.exceptions import TextXSemanticError, TextXSyntaxError


BASE_DIR = os.path.dirname(__file__)
HEURISTICS_DIR = os.path.join(BASE_DIR, "heuristics")
SUPPORTED_TARGETS = {"dotnet"}
SUPPORTED_DEPLOYMENTS = {
    "compose": "Docker",
    "docker": "Docker",
    "dockercompose": "Docker",
    "dockerswarm": "DockerSwarm",
    "k8s": "Kubernetes",
    "kubernetes": "Kubernetes",
    "swarm": "DockerSwarm",
}


@dataclass(frozen=True)
class ValidationProblem:
    message: str
    line: int = None
    column: int = None

    def __str__(self):
        if self.line is None:
            return self.message

        if self.column is None:
            return f"line {self.line}: {self.message}"

        return f"line {self.line}, col {self.column}: {self.message}"


class DslValidationError(ValueError):
    def __init__(self, problems):
        self.problems = tuple(problems)
        super().__init__(format_validation_error(self.problems))


def validate_model(model, source_text: str = None):
    errors = []

    errors.extend(validate_project(model))
    errors.extend(validate_contexts(model, source_text))
    errors.extend(validate_infrastructure(model))
    errors.extend(validate_deployment(model, source_text))
    errors.extend(validate_capabilities(model, source_text))

    if errors:
        raise DslValidationError(errors)


def validate_project(model):
    errors = []

    target = (getattr(model, "target", None) or "dotnet").lower()
    if target not in SUPPORTED_TARGETS:
        errors.append(
            ValidationProblem(
                f"Project target '{getattr(model, 'target', None)}' is not supported. Supported targets: dotnet."
            )
        )

    archetype = getattr(getattr(model, "archetype", None), "value", None)
    supported_archetypes = load_supported_archetypes()
    normalized_archetype = normalize_name(archetype)

    if normalized_archetype and normalized_archetype not in supported_archetypes:
        errors.append(
            ValidationProblem(
                f"Archetype '{archetype}' is not recognized. Supported archetypes: {', '.join(sorted(supported_archetypes.values()))}."
            )
        )

    return errors


def validate_contexts(model, source_text: str = None):
    errors = []
    context_names = []
    known_types = collect_known_types(model)
    errors.extend(validate_global_domain_names(model, source_text))

    for context in getattr(model, "contexts", []) or []:
        context_name = context.name
        normalized_context_name = normalize_name(context_name)
        if normalized_context_name in context_names:
            errors.append(
                problem_from_node(
                    f"Duplicate context name '{context_name}'. Context names must be unique.",
                    context,
                    source_text,
                )
            )
        else:
            context_names.append(normalized_context_name)

        errors.extend(validate_named_collection(context_name, "entity", context.entities, source_text))
        errors.extend(validate_named_collection(context_name, "value object", context.valueObjects, source_text))
        errors.extend(validate_named_collection(context_name, "aggregate", context.aggregates, source_text))
        errors.extend(validate_aggregates(context_name, context.entities, context.aggregates, source_text))
        errors.extend(validate_property_types(context_name, context.entities, context.valueObjects, known_types, source_text))
        for item_label, items in (
            ("entity", context.entities),
            ("value object", context.valueObjects),
        ):
            for item in items or []:
                if not (item.properties or []):
                    errors.append(
                        problem_from_node(
                            f"{item_label.title()} '{item.name}' in context '{context_name}' must define at least one property.",
                            item,
                            source_text,
                        )
                    )
                errors.extend(
                    validate_named_collection(
                        f"{context_name}.{item.name}",
                        f"{item_label} property",
                        item.properties,
                        source_text,
                    )
                )

    return errors


def validate_infrastructure(model):
    infra = getattr(model, "infrastructure", None)
    if not infra:
        return []

    errors = []

    for label in ("database", "cache", "broker"):
        item = getattr(infra, label, None)
        if item and not getattr(item, "type", None):
            errors.append(ValidationProblem(f"Infrastructure {label} must specify a type."))

    supported = {
        "database": {"postgres", "postgresql"},
        "cache": {"redis"},
        "broker": {"rabbitmq"},
    }
    for label, implementations in supported.items():
        item = getattr(infra, label, None)
        value = normalize_name(getattr(item, "type", None))
        if value and value not in implementations:
            errors.append(
                ValidationProblem(
                    f"Infrastructure {label} '{item.type}' is not supported. "
                    f"Supported values: {', '.join(sorted(implementations))}."
                )
            )

    return errors


def validate_global_domain_names(model, source_text: str = None):
    errors = []
    seen_types = {}
    seen_aggregates = {}

    for context in getattr(model, "contexts", []) or []:
        for item in [*(context.entities or []), *(context.valueObjects or [])]:
            normalized = normalize_name(item.name)
            previous = seen_types.get(normalized)
            if previous:
                errors.append(
                    problem_from_node(
                        f"Domain type '{item.name}' in context '{context.name}' conflicts with "
                        f"'{previous[1]}' in context '{previous[0]}'. Generated .NET type names must be globally unique.",
                        item,
                        source_text,
                    )
                )
            else:
                seen_types[normalized] = (context.name, item.name)

        for aggregate in context.aggregates or []:
            normalized = normalize_name(aggregate.name)
            previous = seen_aggregates.get(normalized)
            if previous:
                errors.append(
                    problem_from_node(
                        f"Aggregate '{aggregate.name}' in context '{context.name}' conflicts with "
                        f"aggregate '{previous[1]}' in context '{previous[0]}'.",
                        aggregate,
                        source_text,
                    )
                )
            else:
                seen_aggregates[normalized] = (context.name, aggregate.name)

    return errors


def validate_deployment(model, source_text: str = None):
    deployment = getattr(model, "deployment", None)
    if not deployment:
        return []

    target = getattr(deployment, "target", None)
    if normalize_name(target) in SUPPORTED_DEPLOYMENTS:
        return []

    supported = ", ".join(sorted(set(SUPPORTED_DEPLOYMENTS.values())))
    return [
        problem_from_node(
            f"Deployment target '{target}' is not supported. Supported targets: {supported}.",
            deployment,
            source_text,
        )
    ]


def validate_capabilities(model, source_text: str = None):
    capabilities = getattr(model, "capabilities", None)
    explicit = getattr(capabilities, "capabilities", []) or []
    if not explicit:
        return []

    registry = load_capability_registry()
    available = {normalize_name(name) for name in registry.keys()}
    errors = []
    seen = set()

    for capability in explicit:
        name = normalize_name(capability.name)
        if name in seen:
            errors.append(
                problem_from_node(
                    f"Capability '{capability.name}' is declared more than once.",
                    capability,
                    source_text,
                )
            )
            continue
        seen.add(name)

        if name not in available:
            errors.append(
                problem_from_node(
                    f"Capability '{capability.name}' is not recognized. Available capabilities: {', '.join(sorted(registry.keys()))}.",
                    capability,
                    source_text,
                )
            )
            continue

        implementation = getattr(capability, "implementation", None)
        if not implementation:
            continue

        normalized_implementation = normalize_capability_implementation(name, implementation)
        implementations = {
            normalize_capability_implementation(name, implementation_name)
            for implementation_name in registry.get(name, {}).keys()
        }
        if normalized_implementation not in implementations:
            errors.append(
                problem_from_node(
                    f"Capability '{capability.name}' implementation '{implementation}' is not recognized. Available implementations: {', '.join(sorted(registry.get(name, {}).keys()))}.",
                    capability,
                    source_text,
                )
            )

    return errors


def validate_named_collection(context_name, item_label, items, source_text: str = None):
    errors = []
    seen = set()

    for item in items or []:
        name = normalize_name(item.name)
        if name in seen:
            errors.append(
                problem_from_node(
                    f"Context '{context_name}' contains duplicate {item_label} name '{item.name}'.",
                    item,
                    source_text,
                )
            )
        else:
            seen.add(name)

    return errors


def validate_aggregates(context_name, entities, aggregates, source_text: str = None):
    errors = []
    entity_names = {normalize_name(entity.name): entity.name for entity in entities or []}

    for aggregate in aggregates or []:
        root_entity = getattr(aggregate, "root", None)
        root_name = getattr(root_entity, "name", None)
        if not root_name:
            errors.append(
                problem_from_node(
                    f"Aggregate '{aggregate.name}' in context '{context_name}' must define a root entity.",
                    aggregate,
                    source_text,
                )
            )
            continue

        if normalize_name(root_name) not in entity_names:
            errors.append(
                problem_from_node(
                    f"Aggregate '{aggregate.name}' in context '{context_name}' references unknown root '{root_name}'.",
                    aggregate,
                    source_text,
                )
            )

        child_names = set()
        for child_entity in getattr(aggregate, "children", []) or []:
            child_name = getattr(child_entity, "name", None)
            normalized_child = normalize_name(child_name)
            if normalized_child in child_names:
                errors.append(
                    problem_from_node(
                        f"Aggregate '{aggregate.name}' in context '{context_name}' contains duplicate child '{child_name}'.",
                        aggregate,
                        source_text,
                    )
                )
                continue

            child_names.add(normalized_child)

            if normalized_child not in entity_names:
                errors.append(
                    problem_from_node(
                        f"Aggregate '{aggregate.name}' in context '{context_name}' references unknown child '{child_name}'.",
                        aggregate,
                        source_text,
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
                problem_from_node(
                    f"{item_label.title()} '{item_name}' in context '{context_name}' uses unknown property type '{property_type}' for '{property_name}'.",
                    property_item,
                    source_text,
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
    position = position_from_node(node, source_text)
    if not position:
        return None

    line, column = position
    return f"line {line}, col {column}"


def position_from_node(node, source_text: str = None):
    if not node:
        return None

    position = getattr(node, "_tx_position", None)
    if position is None or source_text is None:
        return None

    line = source_text.count("\n", 0, position) + 1
    last_newline = source_text.rfind("\n", 0, position)
    column = position + 1 if last_newline < 0 else position - last_newline
    return line, column


def problem_from_node(message: str, node=None, source_text: str = None):
    position = position_from_node(node, source_text)
    if not position:
        return ValidationProblem(message)

    line, column = position
    return ValidationProblem(message, line, column)


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


def normalize_capability_implementation(capability: str, value: str):
    normalized = normalize_name(value)

    if capability == "database" and normalized == "postgresql":
        return "postgres"

    if capability == "cqrs" and normalized == "wolverinefx":
        return "wolverine"

    return normalized


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
