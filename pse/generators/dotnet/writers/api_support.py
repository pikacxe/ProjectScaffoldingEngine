import os

from ..structure_helpers import build_namespace
from ..template_loader import render_template


def write_validator_class(path: str, folder: str, name: str, dto_name: str, properties):
    namespace = build_namespace(path, folder)
    dto_namespace = build_namespace(path, "Dtos")

    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            content = f.read()

        if "AbstractValidator" in content and "{{" not in content:
            return

    rules = "".join(
        f"        RuleFor(x => x.{prop_name}).NotEmpty();\n"
        for prop_name in (properties or {}).keys()
    )

    content = render_template(
        "DtoValidator.cs.tmpl",
        {
            "DtoNamespace": dto_namespace,
            "Namespace": namespace,
            "ClassName": name,
            "DtoName": dto_name,
            "Rules": rules,
        },
    )

    with open(path, "w", encoding="utf-8") as f:
        f.write(content)


def write_mapping_config(path: str, folder: str, entities):
    namespace = build_namespace(path, folder)
    project_root = namespace.split(".")[0]
    surface_namespace = namespace.rsplit(".", 1)[0]
    dto_namespace = f"{surface_namespace}.Dtos"
    entity_namespace = f"{project_root}.Domain.Entities"

    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            content = f.read()

        if "TypeAdapterConfig" in content and "{{" not in content:
            return

    mappings = []
    for entity in entities or []:
        dto_name = f"{entity.name}Dto"
        mappings.append(f"        TypeAdapterConfig<{entity.name}, {dto_name}>.NewConfig();\n")
        mappings.append(f"        TypeAdapterConfig<{dto_name}, {entity.name}>.NewConfig();\n")

    content = render_template(
        "MappingConfig.cs.tmpl",
        {
            "DtoNamespace": dto_namespace,
            "EntityNamespace": entity_namespace,
            "Namespace": namespace,
            "Mappings": "".join(mappings),
        },
    )

    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
