import os

from .structure_helpers import ensure_dir, ensure_placeholder, remove_placeholder
from .structure_writers import (
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

    created = create_context_api_files(
        api_root,
        contexts,
        use_mapping=capability_enabled(ctx, "mapping"),
        cqrs_implementation=capability_value(ctx, "cqrs"),
    )
    if capability_enabled(ctx, "validation"):
        create_validator_files(api_root, contexts)
    if capability_enabled(ctx, "mapping"):
        create_mapping_files(api_root, contexts)

    if not created:
        ensure_placeholder(api_root, "Controllers", "ExampleController.cs", "API controller skeleton")
        ensure_placeholder(api_root, "Dtos", "ExampleDto.cs", "API DTO skeleton")
        ensure_placeholder(api_root, "Contracts", "ExampleRequest.cs", "API contract request skeleton")
        ensure_placeholder(api_root, "Contracts", "ExampleResponse.cs", "API contract response skeleton")


def create_presentation_structure(presentation_root: str, contexts, ctx=None):
    ensure_dir(presentation_root, "Controllers")
    ensure_dir(presentation_root, "Dtos")
    ensure_dir(presentation_root, "Contracts")
    if capability_enabled(ctx, "validation"):
        ensure_dir(presentation_root, "Validators")
    if capability_enabled(ctx, "mapping"):
        ensure_dir(presentation_root, "Mapping")

    created = create_context_api_files(
        presentation_root,
        contexts,
        use_mapping=capability_enabled(ctx, "mapping"),
        cqrs_implementation=capability_value(ctx, "cqrs"),
    )
    if capability_enabled(ctx, "validation"):
        create_validator_files(presentation_root, contexts)
    if capability_enabled(ctx, "mapping"):
        create_mapping_files(presentation_root, contexts)

    if not created:
        ensure_placeholder(presentation_root, "Controllers", "ExampleController.cs", "Presentation controller skeleton")
        ensure_placeholder(presentation_root, "Dtos", "ExampleDto.cs", "Presentation DTO skeleton")
        ensure_placeholder(presentation_root, "Contracts", "ExampleRequest.cs", "Presentation request skeleton")
        ensure_placeholder(presentation_root, "Contracts", "ExampleResponse.cs", "Presentation response skeleton")


def create_application_structure(app_root: str, contexts, ctx=None):
    ensure_dir(app_root, "Interfaces")
    ensure_dir(app_root, "Services")
    cqrs_implementation = capability_value(ctx, "cqrs")
    if cqrs_implementation:
        ensure_dir(app_root, "Cqrs")

    created = create_application_service_files(app_root, contexts)
    cqrs_created = create_cqrs_files(app_root, contexts, cqrs_implementation)

    if not created and not cqrs_created:
        ensure_placeholder(app_root, "Interfaces", "IExampleService.cs", "Application service interface")
        ensure_placeholder(app_root, "Services", "ExampleService.cs", "Application service implementation")


def create_domain_structure(domain_root: str, contexts):
    ensure_dir(domain_root, "Entities")
    ensure_dir(domain_root, "ValueObjects")
    ensure_dir(domain_root, "Repositories")
    ensure_dir(domain_root, "Events")
    created = create_domain_files(domain_root, contexts)

    if not created:
        ensure_placeholder(domain_root, "Entities", "ExampleEntity.cs", "Domain entity")
        ensure_placeholder(domain_root, "ValueObjects", "ExampleValueObject.cs", "Domain value object")
        ensure_placeholder(domain_root, "Repositories", "IExampleRepository.cs", "Repository interface")
        ensure_placeholder(domain_root, "Events", "ExampleDomainEvent.cs", "Domain event")


def create_infrastructure_structure(infra_root: str, contexts):
    ensure_dir(infra_root, "Persistence")
    ensure_dir(infra_root, "Repositories")
    ensure_dir(infra_root, "Messaging")
    ensure_placeholder(infra_root, "Persistence", "PersistenceOptions.cs", "Infrastructure persistence options")
    ensure_placeholder(infra_root, "Messaging", "MessageBusOptions.cs", "Infrastructure messaging options")

    created = create_repository_implementations(infra_root, contexts)
    if not created:
        ensure_placeholder(infra_root, "Repositories", "ExampleRepository.cs", "Repository implementation")
    else:
        remove_placeholder(infra_root, "Repositories", "ExampleRepository.cs")


def create_tests_structure(tests_root: str, contexts):
    ensure_dir(tests_root, "Unit")
    ensure_dir(tests_root, "Integration")
    created = create_tests_files(tests_root, contexts)

    if not created:
        ensure_placeholder(tests_root, "Unit", "ExampleUnitTests.cs", "Unit test skeleton")
        ensure_placeholder(tests_root, "Integration", "ExampleIntegrationTests.cs", "Integration test skeleton")
    else:
        remove_placeholder(tests_root, "Unit", "ExampleUnitTests.cs")
        remove_placeholder(tests_root, "Integration", "ExampleIntegrationTests.cs")


def create_context_api_files(root: str, contexts, root_prefix: str = "", use_mapping: bool = False, cqrs_implementation: str = None):
    created = False
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
            write_csharp_class(dto_path, "Dtos", dto_name, properties=entity.properties)
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
    for context in contexts or []:
        if not context:
            continue
        for entity in context.entities:
            entity_path = os.path.join(root, root_prefix, "Entities", f"{entity.name}.cs")
            write_csharp_class(entity_path, "Entities", entity.name, properties=entity.properties)
            repo_name = f"I{entity.name}Repository"
            repo_path = os.path.join(root, root_prefix, "Repositories", f"{repo_name}.cs")
            write_repository_interface(repo_path, "Repositories", repo_name, entity.name, pick_id_type(entity.properties))
            created = True

        for value_object in context.value_objects:
            vo_path = os.path.join(root, root_prefix, "ValueObjects", f"{value_object.name}.cs")
            write_csharp_class(vo_path, "ValueObjects", value_object.name, properties=value_object.properties)
            created = True

    return created


def create_repository_implementations(root: str, contexts, root_prefix: str = ""):
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


def capability_enabled(ctx, name: str):
    capabilities = getattr(getattr(ctx, "capabilities", None), "capabilities", {}) or {}
    return name.lower() in capabilities


def capability_value(ctx, name: str):
    capabilities = getattr(getattr(ctx, "capabilities", None), "capabilities", {}) or {}
    capability = capabilities.get(name.lower())
    return getattr(capability, "value", None)
