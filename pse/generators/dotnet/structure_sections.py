import os

from .capabilities import capability_enabled, capability_value
from .structure_helpers import ensure_dir
from .writers import (
    write_aggregate_class,
    write_controller,
    write_csharp_class,
    write_mediatr_cqrs_class,
    write_mapping_config,
    write_repository_class,
    write_repository_interface,
    write_service_class,
    write_service_interface,
    write_wolverine_cqrs_class,
    write_test_class,
    write_validator_class,
)
from .structure_helpers import pick_id_property_name, pick_id_type


def create_api_structure(api_root: str, contexts, ctx=None):
    ensure_dir(api_root, "Controllers")
    ensure_dir(api_root, "Dtos")
    ensure_dir(api_root, "Contracts")
    if capability_enabled(ctx, "validation"):
        ensure_dir(api_root, "Validators")
    if capability_enabled(ctx, "mapping"):
        ensure_dir(api_root, "Mapping")

    create_context_api_files(
        api_root,
        contexts,
        use_mapping=capability_enabled(ctx, "mapping"),
        cqrs_implementation=capability_value(ctx, "cqrs"),
    )
    if capability_enabled(ctx, "validation"):
        create_validator_files(api_root, contexts)
    if capability_enabled(ctx, "mapping"):
        create_mapping_files(api_root, contexts)



def create_presentation_structure(presentation_root: str, contexts, ctx=None):
    ensure_dir(presentation_root, "Controllers")
    ensure_dir(presentation_root, "Dtos")
    ensure_dir(presentation_root, "Contracts")
    if capability_enabled(ctx, "validation"):
        ensure_dir(presentation_root, "Validators")
    if capability_enabled(ctx, "mapping"):
        ensure_dir(presentation_root, "Mapping")

    create_context_api_files(
        presentation_root,
        contexts,
        use_mapping=capability_enabled(ctx, "mapping"),
        cqrs_implementation=capability_value(ctx, "cqrs"),
    )
    if capability_enabled(ctx, "validation"):
        create_validator_files(presentation_root, contexts)
    if capability_enabled(ctx, "mapping"):
        create_mapping_files(presentation_root, contexts)



def create_application_structure(app_root: str, contexts, ctx=None):
    ensure_dir(app_root, "Interfaces")
    ensure_dir(app_root, "Services")
    cqrs_implementation = capability_value(ctx, "cqrs")
    if cqrs_implementation:
        ensure_dir(app_root, "Cqrs")
    cleanup_inactive_cqrs_files(app_root, contexts, cqrs_implementation)

    create_application_service_files(app_root, contexts)
    create_cqrs_files(app_root, contexts, cqrs_implementation)



def cleanup_inactive_cqrs_files(app_root: str, contexts, implementation: str = None):
    active_suffix = {
        "mediatr": "Requests.cs",
        "wolverine": "Messages.cs",
    }.get(implementation)
    cqrs_root = os.path.join(app_root, "Cqrs")
    if not os.path.isdir(cqrs_root):
        return

    expected = {
        f"{entity.name}{active_suffix}"
        for context in contexts or []
        for entity in getattr(context, "entities", []) or []
        if active_suffix
    }
    for file_name in os.listdir(cqrs_root):
        is_generated_cqrs = file_name.endswith(("Requests.cs", "Messages.cs"))
        if is_generated_cqrs and file_name not in expected:
            os.remove(os.path.join(cqrs_root, file_name))


def create_domain_structure(domain_root: str, contexts):
    ensure_dir(domain_root, "Aggregates")
    ensure_dir(domain_root, "Entities")
    ensure_dir(domain_root, "ValueObjects")
    ensure_dir(domain_root, "Repositories")
    ensure_dir(domain_root, "Events")
    create_domain_files(domain_root, contexts)



def create_infrastructure_structure(infra_root: str, contexts, ctx=None):
    ensure_dir(infra_root, "Persistence")
    ensure_dir(infra_root, "Repositories")
    ensure_dir(infra_root, "Messaging")
    create_repository_implementations(
        infra_root,
        contexts,
        use_database=capability_value(ctx, "database") == "postgres",
    )


def create_tests_structure(tests_root: str, contexts):
    ensure_dir(tests_root, "Unit")
    ensure_dir(tests_root, "Integration")
    create_tests_files(tests_root, contexts)



def create_context_api_files(root: str, contexts, root_prefix: str = "", use_mapping: bool = False, cqrs_implementation: str = None):
    created = False
    entity_names, value_object_names = domain_type_names(contexts)
    project_name = os.path.basename(root).split(".")[0]
    for context in contexts or []:
        if not context:
            continue
        for entity in context.entities:
            controller_name = f"{entity.name}Controller"
            dto_name = f"{entity.name}Dto"
            controller_path = os.path.join(root, root_prefix, "Controllers", f"{controller_name}.cs")
            dto_path = os.path.join(root, root_prefix, "Dtos", f"{dto_name}.cs")

            write_controller(
                controller_path,
                "Controllers",
                controller_name,
                entity,
                dto_name,
                use_mapping=use_mapping,
                cqrs_implementation=cqrs_implementation,
            )
            write_csharp_class(
                dto_path,
                "Dtos",
                dto_name,
                properties=entity.properties,
                additional_usings=property_type_usings(
                    entity.properties,
                    entity_names,
                    value_object_names,
                    f"{project_name}.Domain",
                ),
            )
            created = True

    return created


def create_validator_files(root: str, contexts, root_prefix: str = ""):
    created = False
    for context in contexts or []:
        if not context:
            continue
        for entity in context.entities:
            dto_name = f"{entity.name}Dto"
            validator_name = f"{dto_name}Validator"
            validator_path = os.path.join(root, root_prefix, "Validators", f"{validator_name}.cs")
            write_validator_class(validator_path, "Validators", validator_name, dto_name, entity.properties)
            created = True

    return created


def create_mapping_files(root: str, contexts, root_prefix: str = ""):
    entities = [
        entity
        for context in contexts or []
        if context
        for entity in context.entities
    ]
    if not entities:
        return False

    mapping_path = os.path.join(root, root_prefix, "Mapping", "MappingConfig.cs")
    write_mapping_config(mapping_path, "Mapping", entities)
    return True


def create_application_service_files(root: str, contexts, root_prefix: str = ""):
    created = False
    for context in contexts or []:
        if not context:
            continue
        for entity in context.entities:
            interface_name = f"I{entity.name}Service"
            class_name = f"{entity.name}Service"
            interface_path = os.path.join(root, root_prefix, "Interfaces", f"{interface_name}.cs")
            class_path = os.path.join(root, root_prefix, "Services", f"{class_name}.cs")
            write_service_interface(
                interface_path,
                "Interfaces",
                interface_name,
                entity.name,
                pick_id_type(entity.properties),
            )
            write_service_class(
                class_path,
                "Services",
                class_name,
                interface_name,
                entity.name,
                pick_id_type(entity.properties),
                pick_id_property_name(entity.properties),
            )
            created = True

    return created


def create_cqrs_files(root: str, contexts, implementation: str = None, root_prefix: str = ""):
    if not implementation:
        return False

    created = False
    for context in contexts or []:
        if not context:
            continue
        for entity in context.entities:
            if implementation == "mediatr":
                cqrs_path = os.path.join(root, root_prefix, "Cqrs", f"{entity.name}Requests.cs")
                write_mediatr_cqrs_class(
                    cqrs_path,
                    "Cqrs",
                    entity.name,
                    pick_id_type(entity.properties),
                )
                created = True
            elif implementation == "wolverine":
                cqrs_path = os.path.join(root, root_prefix, "Cqrs", f"{entity.name}Messages.cs")
                write_wolverine_cqrs_class(
                    cqrs_path,
                    "Cqrs",
                    entity.name,
                    pick_id_type(entity.properties),
                )
                created = True

    return created


def create_domain_files(root: str, contexts, root_prefix: str = ""):
    created = False
    entity_names, value_object_names = domain_type_names(contexts)
    domain_namespace = os.path.basename(root).split(".")[0] + ".Domain"
    for context in contexts or []:
        if not context:
            continue
        for entity in context.entities:
            entity_path = os.path.join(root, root_prefix, "Entities", f"{entity.name}.cs")
            write_csharp_class(
                entity_path,
                "Entities",
                entity.name,
                properties=entity.properties,
                additional_usings=property_type_usings(
                    entity.properties,
                    entity_names,
                    value_object_names,
                    domain_namespace,
                ),
            )
            repo_name = f"I{entity.name}Repository"
            repo_path = os.path.join(root, root_prefix, "Repositories", f"{repo_name}.cs")
            write_repository_interface(repo_path, "Repositories", repo_name, entity.name, pick_id_type(entity.properties))
            created = True

        for value_object in context.value_objects:
            vo_path = os.path.join(root, root_prefix, "ValueObjects", f"{value_object.name}.cs")
            write_csharp_class(
                vo_path,
                "ValueObjects",
                value_object.name,
                properties=value_object.properties,
                additional_usings=property_type_usings(
                    value_object.properties,
                    entity_names,
                    value_object_names,
                    domain_namespace,
                ),
            )
            created = True

        for aggregate in context.aggregates:
            aggregate_path = os.path.join(root, root_prefix, "Aggregates", f"{aggregate.name}.cs")
            write_aggregate_class(aggregate_path, "Aggregates", aggregate)
            created = True

    return created


def domain_type_names(contexts):
    entity_names = {
        entity.name.lower()
        for context in contexts or []
        for entity in context.entities
    }
    value_object_names = {
        value_object.name.lower()
        for context in contexts or []
        for value_object in context.value_objects
    }
    return entity_names, value_object_names


def property_type_usings(properties, entity_names, value_object_names, domain_namespace):
    property_types = {value.lower() for value in (properties or {}).values()}
    usings = []
    if property_types & entity_names:
        usings.append(f"{domain_namespace}.Entities")
    if property_types & value_object_names:
        usings.append(f"{domain_namespace}.ValueObjects")
    return usings


def create_repository_implementations(root: str, contexts, root_prefix: str = "", use_database: bool = False):
    created = False
    for context in contexts or []:
        if not context:
            continue
        for entity in context.entities:
            repo_name = f"{entity.name}Repository"
            repo_path = os.path.join(root, root_prefix, "Repositories", f"{repo_name}.cs")
            interface_name = f"I{entity.name}Repository"
            write_repository_class(
                repo_path,
                "Repositories",
                repo_name,
                interface_name,
                entity.name,
                pick_id_type(entity.properties),
                pick_id_property_name(entity.properties),
                use_database=use_database,
            )
            created = True

    return created


def create_tests_files(root: str, contexts):
    created = False
    for context in contexts or []:
        if not context:
            continue
        for entity in context.entities:
            test_name = f"{entity.name}Tests"
            test_path = os.path.join(root, "Unit", f"{test_name}.cs")
            write_test_class(test_path, "Unit", test_name, entity)
            created = True

    return created
