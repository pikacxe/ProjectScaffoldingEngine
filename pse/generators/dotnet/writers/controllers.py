import os

from .controller_cqrs import (
    build_mediatr_controller_methods,
    build_wolverine_controller_methods,
)
from .controller_mapping import build_manual_mapping_methods, map_expression
from ..structure_helpers import build_namespace, pick_id_property_name, pick_id_type
from ..template_loader import render_template


def write_controller(path: str, folder: str, name: str, entity, dto_name: str, use_mapping: bool = False, cqrs_implementation: str = None):
    namespace = build_namespace(path, folder)
    entity_namespace = replace_surface_namespace(namespace, "Domain.Entities")
    service_namespace = replace_surface_namespace(namespace, "Application.Interfaces")
    cqrs_namespace = replace_surface_namespace(namespace, "Application.Cqrs")
    dto_namespace = build_namespace(path, "Dtos")
    id_type = pick_id_type(entity.properties)
    id_property_name = pick_id_property_name(entity.properties)
    cqrs_implementation = (cqrs_implementation or "").lower()

    if controller_is_current(path, entity.name, use_mapping, cqrs_implementation):
        return

    methods = build_controller_methods(
        entity_name=entity.name,
        dto_name=dto_name,
        id_type=id_type,
        id_property_name=id_property_name,
        properties=list(entity.properties.keys()),
        use_mapping=use_mapping,
        cqrs_implementation=cqrs_implementation,
    )
    using_lines = build_controller_usings(
        dto_namespace,
        entity_namespace,
        service_namespace,
        cqrs_namespace,
        use_mapping,
        cqrs_implementation,
    )
    content = render_template(
        "Controller.cs.tmpl",
        {
            "UsingLines": f"{using_lines}\n",
            "Namespace": namespace,
            "ControllerName": name,
            "Methods": methods,
        },
    )

    with open(path, "w", encoding="utf-8") as f:
        f.write(content)


def replace_surface_namespace(namespace: str, target: str):
    for surface in ("API.Controllers", "Presentation.Controllers", "Gateway.Controllers"):
        suffix = f".{surface}"
        if namespace.endswith(suffix):
            return f"{namespace[:-len(suffix)]}.{target}"
    return namespace


def controller_is_current(path, entity_name, use_mapping, cqrs_implementation):
    if not os.path.exists(path):
        return False

    with open(path, "r", encoding="utf-8") as f:
        content = f.read()

    has_expected_dependency = (
        (cqrs_implementation == "mediatr" and "IMediator" in content)
        or (cqrs_implementation == "wolverine" and "IMessageBus" in content)
        or (
            cqrs_implementation not in {"mediatr", "wolverine"}
            and f"I{entity_name}Service" in content
        )
    )
    has_expected_mapping = use_mapping or ("ToDto(" in content and "ToEntity(" in content)
    return (
        "private readonly" in content
        and "{{" not in content
        and "TODO" not in content
        and has_expected_mapping
        and has_expected_dependency
    )


def build_controller_usings(
    dto_namespace,
    entity_namespace,
    service_namespace,
    cqrs_namespace,
    use_mapping,
    cqrs_implementation,
):
    lines = [
        "using System.Collections.Generic;",
        "using System.Linq;",
        "using System.Threading.Tasks;",
        f"using {dto_namespace};",
        f"using {entity_namespace};",
    ]
    if cqrs_implementation in {"mediatr", "wolverine"}:
        lines.append(f"using {cqrs_namespace};")
    else:
        lines.append(f"using {service_namespace};")

    if cqrs_implementation == "mediatr":
        lines.append("using MediatR;")
    elif cqrs_implementation == "wolverine":
        lines.append("using Wolverine;")
    if use_mapping:
        lines.append("using Mapster;")

    return "\n".join(lines) + "\n"


def build_controller_methods(entity_name: str, dto_name: str, id_type: str, id_property_name: str, properties, use_mapping: bool = False, cqrs_implementation: str = None):
    if cqrs_implementation == "mediatr":
        return build_mediatr_controller_methods(
            entity_name, dto_name, id_type, id_property_name, properties, use_mapping
        )

    if cqrs_implementation == "wolverine":
        return build_wolverine_controller_methods(
            entity_name, dto_name, id_type, id_property_name, properties, use_mapping
        )

    service_field_name = f"_{entity_name[0].lower()}{entity_name[1:]}Service"
    service_parameter_name = f"{entity_name[0].lower()}{entity_name[1:]}Service"
    service_interface_name = f"I{entity_name}Service"
    core_methods = render_template(
        "ServiceControllerMethods.cs.tmpl",
        {
            "ServiceInterface": service_interface_name,
            "ServiceField": service_field_name,
            "ServiceParameter": service_parameter_name,
            "EntityName": entity_name,
            "DtoName": dto_name,
            "IdType": id_type,
            "IdPropertyName": id_property_name,
            "EntityToDto": map_expression("entity", dto_name, use_mapping),
            "RequestToEntity": map_expression("request", entity_name, use_mapping),
            "CreatedToDto": map_expression("created", dto_name, use_mapping),
        },
    )

    if use_mapping:
        return core_methods

    return core_methods + build_manual_mapping_methods(entity_name, dto_name, properties)
