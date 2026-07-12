from .common import deployment_target
from .compose import create_compose_deployment
from .kubernetes import create_kubernetes_deployment
from .swarm import create_swarm_deployment


def create_deployment(ctx):
    target = deployment_target(ctx)

    if target is None:
        return
    if target == "docker":
        create_compose_deployment(ctx)
        return
    if target == "swarm":
        create_swarm_deployment(ctx)
        return
    if target == "kubernetes":
        create_kubernetes_deployment(ctx)
        return

    raise ValueError(f"Unsupported deployment target: {target}")


__all__ = ["create_deployment"]
