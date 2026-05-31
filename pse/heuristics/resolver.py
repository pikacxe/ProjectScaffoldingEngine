import yaml

from model.capability import CapabilityGraph, Capability


def resolve_capabilities(ctx):
    graph = CapabilityGraph()

    archetype = ctx.architecture.project.archetype.lower()

    preset = ctx.presets.get(archetype, {})

    caps = preset.get("capabilities", {})

    # 1. load preset capabilities
    for k, v in caps.items():
        graph.capabilities[k] = Capability(
            name=k,
            value=v,
            source="preset"
        )

    # 1b. apply explicit capability selections
    explicit = getattr(ctx.architecture, "capabilities", []) or []
    registry = load_capability_registry()

    for cap_name in explicit:
        name = cap_name.lower()
        implementation = pick_default_implementation(name, caps, registry)

        graph.capabilities[name] = Capability(
            name=name,
            value=implementation or "unresolved",
            source="explicit"
        )

    # 2. infer from infrastructure
    infra = ctx.architecture.infrastructure

    if infra:
        if infra.database:
            graph.capabilities["database"] = Capability(
                "database",
                infra.database.type.lower(),
                "inferred"
            )

        if infra.cache:
            graph.capabilities["cache"] = Capability(
                "cache",
                infra.cache.type.lower(),
                "inferred"
            )

        if infra.broker:
            graph.capabilities["messaging"] = Capability(
                "messaging",
                infra.broker.type.lower(),
                "inferred"
            )

    # 3. default fallbacks
    graph.capabilities.setdefault(
        "logging",
        Capability("logging", "serilog", "default")
    )

    graph.capabilities.setdefault(
        "validation",
        Capability("validation", "fluentvalidation", "default")
    )

    return graph


def load_capability_registry():
    with open("heuristics/capabilities.yaml") as f:
        return yaml.safe_load(f) or {}


def pick_default_implementation(name, preset_caps, registry):
    if name in preset_caps:
        return preset_caps[name]

    implementations = registry.get(name, {})
    if len(implementations) == 1:
        return next(iter(implementations.keys()))

    return None