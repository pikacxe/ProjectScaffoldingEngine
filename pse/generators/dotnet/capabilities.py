def capability_enabled(ctx, name: str):
    return name.lower() in capability_registry(ctx)


def capability_value(ctx, name: str):
    capability = capability_registry(ctx).get(name.lower())
    return getattr(capability, "value", None)


def capability_registry(ctx):
    return getattr(getattr(ctx, "capabilities", None), "capabilities", {}) or {}
