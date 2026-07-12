"""Shared entity and DTO mapping code builders."""

from ..template_loader import render_template


def build_manual_mapping_methods(entity_name: str, dto_name: str, properties):
    to_dto_assignments = build_object_initializer("entity", dto_name, properties)
    to_entity_assignments = build_object_initializer("dto", entity_name, properties)
    return render_template(
        "ControllerManualMapping.cs.tmpl",
        {
            "EntityName": entity_name,
            "DtoName": dto_name,
            "ToDtoAssignments": to_dto_assignments,
            "ToEntityAssignments": to_entity_assignments,
        },
    )


def map_expression(source_name: str, target_name: str, use_mapping: bool):
    if use_mapping:
        return f"{source_name}.Adapt<{target_name}>()"
    if target_name.endswith("Dto"):
        return f"ToDto({source_name})"
    return f"ToEntity({source_name})"


def build_object_initializer(source_name: str, target_name: str, properties):
    return "".join(
        f"            {prop_name} = {source_name}.{prop_name},\n"
        for prop_name in properties or []
    )
