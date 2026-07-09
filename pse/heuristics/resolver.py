import os

import yaml

from pse.model.capability import CapabilityGraph, Capability


HEURISTICS_DIR = os.path.dirname(__file__)


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

    for selected in explicit:
        name = getattr(selected, "name", selected).lower()
        requested = getattr(selected, "implementation", None)
        implementation = (
            normalize_implementation(name, requested)
            if requested
            else pick_default_implementation(name, caps, registry)
        )

        graph.capabilities[name] = Capability(
            name=name,
            value=implementation or "unresolved",
            source="explicit"
        )

    # 2. infer from infrastructure
    infra = ctx.architecture.infrastructure

    if infra:
        if infra.database:
            db_type = normalize_implementation("database", infra.database.type)
            graph.capabilities["database"] = Capability(
                "database",
                db_type,
                "inferred"
            )

        if infra.cache:
            cache_type = normalize_implementation("cache", infra.cache.type)
            graph.capabilities["cache"] = Capability(
                "cache",
                cache_type,
                "inferred"
            )

        if infra.broker:
            broker_type = normalize_implementation("messaging", infra.broker.type)
            graph.capabilities["messaging"] = Capability(
                "messaging",
                broker_type,
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
    with open(os.path.join(HEURISTICS_DIR, "capabilities.yaml"), "r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def pick_default_implementation(name, preset_caps, registry):
    if name in preset_caps:
        return preset_caps[name]

    implementations = registry.get(name, {})
    for implementation, metadata in implementations.items():
        if isinstance(metadata, dict) and metadata.get("default"):
            return implementation

    if len(implementations) == 1:
        return next(iter(implementations.keys()))

    return None


def normalize_implementation(capability: str, value: str):
    if not value:
        return "unresolved"

    normalized = value.lower()

    if capability == "database" and normalized == "postgresql":
        return "postgres"

    if capability == "cqrs" and normalized == "wolverinefx":
        return "wolverine"

    return normalized
