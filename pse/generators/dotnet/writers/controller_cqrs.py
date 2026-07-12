"""Controller method builders for MediatR and Wolverine transports."""

from .controller_mapping import build_manual_mapping_methods, map_expression
from ..template_loader import render_template


def build_mediatr_controller_methods(
    entity_name: str,
    dto_name: str,
    id_type: str,
    id_property_name: str,
    properties,
    use_mapping: bool = False,
):
    return build_cqrs_controller_methods(
        "MediatRControllerMethods.cs.tmpl",
        entity_name,
        dto_name,
        id_type,
        id_property_name,
        properties,
        use_mapping,
    )


def build_wolverine_controller_methods(
    entity_name: str,
    dto_name: str,
    id_type: str,
    id_property_name: str,
    properties,
    use_mapping: bool = False,
):
    return build_cqrs_controller_methods(
        "WolverineControllerMethods.cs.tmpl",
        entity_name,
        dto_name,
        id_type,
        id_property_name,
        properties,
        use_mapping,
    )


def build_cqrs_controller_methods(
    template_name,
    entity_name,
    dto_name,
    id_type,
    id_property_name,
    properties,
    use_mapping,
):
    core_methods = render_template(
        template_name,
        {
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
