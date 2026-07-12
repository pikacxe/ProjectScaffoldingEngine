import os
import re
from dataclasses import dataclass

import yaml


TARGET_ALIASES = {
    "docker": "docker",
    "dockercompose": "docker",
    "compose": "docker",
    "dockerswarm": "swarm",
    "swarm": "swarm",
    "kubernetes": "kubernetes",
    "k8s": "kubernetes",
}


@dataclass(frozen=True)
class DeploymentSpec:
    project_name: str
    app_name: str
    entrypoint_project: str
    image: str
    dotnet_version: str
    postgres_version: str
    redis_version: str
    rabbitmq_version: str
    has_database: bool
    has_cache: bool
    has_broker: bool

    @classmethod
    def from_context(cls, ctx):
        project = ctx.architecture.project
        infra = ctx.architecture.infrastructure
        app_name = resource_name(project.name)
        entrypoint_layer = {
            "WebApi": "API",
            "CleanArchitecture": "Presentation",
        }.get(project.archetype)

        if not entrypoint_layer:
            raise ValueError(
                f"Deployment generation is not supported for archetype '{project.archetype}' "
                "because it has no generated web entrypoint."
            )

        return cls(
            project_name=project.name,
            app_name=app_name,
            entrypoint_project=f"{project.name}.{entrypoint_layer}",
            image=f"{app_name}:latest",
            dotnet_version=str(ctx.versions.get("dotnet", "10.0")),
            postgres_version=str(ctx.versions.get("postgres", "17")),
            redis_version=str(ctx.versions.get("redis", "8")),
            rabbitmq_version=str(ctx.versions.get("rabbitmq", "4-management")),
            has_database=bool(infra and infra.database),
            has_cache=bool(infra and infra.cache),
            has_broker=bool(infra and infra.broker),
        )


def deployment_target(ctx):
    deployment = getattr(ctx.architecture, "deployment", None)
    raw_target = getattr(deployment, "target", None)
    if not raw_target:
        return None
    return TARGET_ALIASES.get(normalize_target(raw_target), normalize_target(raw_target))


def normalize_target(value):
    return re.sub(r"[^a-z0-9]", "", str(value).lower())


def resource_name(value):
    normalized = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
    return normalized or "pse-app"


def labels(spec, component):
    return {
        "app.kubernetes.io/name": spec.app_name,
        "app.kubernetes.io/component": component,
        "app.kubernetes.io/managed-by": "pse",
    }


def write_yaml(path, document):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as handle:
        yaml.safe_dump(document, handle, sort_keys=False, default_flow_style=False)


def write_yaml_documents(path, documents):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as handle:
        yaml.safe_dump_all(documents, handle, sort_keys=False, default_flow_style=False)


def write_text(path, content):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as handle:
        handle.write(content if content.endswith("\n") else content + "\n")
