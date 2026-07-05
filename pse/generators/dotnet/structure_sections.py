import os

from .structure_helpers import ensure_dir, ensure_placeholder, remove_placeholder
from .structure_writers import write_controller, write_csharp_class, write_repository_class, write_repository_interface, write_test_class
from .structure_helpers import pick_id_type


def create_api_structure(api_root: str, contexts):
    ensure_dir(api_root, "Controllers")
    ensure_dir(api_root, "Dtos")
    ensure_dir(api_root, "Contracts")
    created = create_context_api_files(api_root, contexts)

    if not created:
        ensure_placeholder(api_root, "Controllers", "ExampleController.cs", "API controller skeleton")
        ensure_placeholder(api_root, "Dtos", "ExampleDto.cs", "API DTO skeleton")
        ensure_placeholder(api_root, "Contracts", "ExampleRequest.cs", "API contract request skeleton")
        ensure_placeholder(api_root, "Contracts", "ExampleResponse.cs", "API contract response skeleton")


def create_presentation_structure(presentation_root: str, contexts):
    ensure_dir(presentation_root, "Controllers")
    ensure_dir(presentation_root, "Dtos")
    ensure_dir(presentation_root, "Contracts")
    created = create_context_api_files(presentation_root, contexts)

    if not created:
        ensure_placeholder(presentation_root, "Controllers", "ExampleController.cs", "Presentation controller skeleton")
        ensure_placeholder(presentation_root, "Dtos", "ExampleDto.cs", "Presentation DTO skeleton")
        ensure_placeholder(presentation_root, "Contracts", "ExampleRequest.cs", "Presentation request skeleton")
        ensure_placeholder(presentation_root, "Contracts", "ExampleResponse.cs", "Presentation response skeleton")


def create_application_structure(app_root: str, contexts):
    ensure_dir(app_root, "Interfaces")
    ensure_dir(app_root, "Services")
    ensure_dir(app_root, "UseCases")
    created = create_use_case_files(app_root, contexts)

    if not created:
        ensure_placeholder(app_root, "Interfaces", "IExampleService.cs", "Application service interface")
        ensure_placeholder(app_root, "Services", "ExampleService.cs", "Application service implementation")
        ensure_placeholder(app_root, "UseCases", "ExampleUseCase.cs", "Application use case")


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


def create_context_api_files(root: str, contexts, root_prefix: str = ""):
    created = False
    for context in contexts or []:
        if not context:
            continue
        for entity in context.entities:
            controller_name = f"{entity.name}Controller"
            dto_name = f"{entity.name}Dto"
            controller_path = os.path.join(root, root_prefix, "Controllers", f"{controller_name}.cs")
            dto_path = os.path.join(root, root_prefix, "Dtos", f"{dto_name}.cs")

            write_controller(controller_path, "Controllers", controller_name, entity, dto_name)
            write_csharp_class(dto_path, "Dtos", dto_name, properties=entity.properties)
            created = True

    return created


def create_use_case_files(root: str, contexts, root_prefix: str = ""):
    created = False
    for context in contexts or []:
        if not context:
            continue
        for entity in context.entities:
            use_case_name = f"{entity.name}UseCase"
            use_case_path = os.path.join(root, root_prefix, "UseCases", f"{use_case_name}.cs")
            write_csharp_class(use_case_path, "UseCases", use_case_name)
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
            write_repository_class(repo_path, "Repositories", repo_name, interface_name, entity.name, pick_id_type(entity.properties))
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
            write_test_class(test_path, "Unit", test_name, entity.name)
            created = True

    return created