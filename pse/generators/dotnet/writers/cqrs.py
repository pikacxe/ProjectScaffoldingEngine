import os

from ..structure_helpers import build_namespace
from ..template_loader import render_template


def write_mediatr_cqrs_class(path: str, folder: str, entity_name: str, id_type: str):
    write_cqrs_class(path, folder, entity_name, id_type, "MediatRRequests.cs.tmpl")


def write_wolverine_cqrs_class(path: str, folder: str, entity_name: str, id_type: str):
    write_cqrs_class(path, folder, entity_name, id_type, "WolverineMessages.cs.tmpl")


def write_cqrs_class(path: str, folder: str, entity_name: str, id_type: str, template_name: str):
    namespace = build_namespace(path, folder)
    project_root = namespace.split(".")[0]

    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            content = f.read()

        if "Handler" in content and "{{" not in content and "TODO" not in content:
            return

    content = render_template(
        template_name,
        {
            "Namespace": namespace,
            "DomainNamespace": f"{project_root}.Domain",
            "InterfaceNamespace": f"{project_root}.Application.Interfaces",
            "EntityName": entity_name,
            "IdType": id_type,
        },
    )

    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
