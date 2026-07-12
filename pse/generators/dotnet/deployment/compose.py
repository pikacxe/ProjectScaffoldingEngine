import os

from .common import DeploymentSpec, write_yaml
from .dockerfile import write_dockerfile
from .services import app_environment, compose_dependencies


def create_compose_deployment(ctx):
    spec = DeploymentSpec.from_context(ctx)
    write_dockerfile(ctx, spec)

    dependency_services, volumes = compose_dependencies(spec)
    depends_on = {
        name: {"condition": "service_healthy"}
        for name in dependency_services
    }
    app = {
        "build": {"context": ".", "dockerfile": "Dockerfile"},
        "image": spec.image,
        "ports": ["8080:8080"],
        "environment": app_environment(spec),
        "networks": ["backend"],
        "restart": "unless-stopped",
    }
    if depends_on:
        app["depends_on"] = depends_on

    document = {
        "services": {spec.app_name: app, **dependency_services},
        "networks": {"backend": {"driver": "bridge"}},
    }
    if volumes:
        document["volumes"] = volumes

    write_yaml(os.path.join(ctx.output_dir, "docker-compose.yml"), document)
