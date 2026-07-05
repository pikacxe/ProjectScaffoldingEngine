import os

from .structure_helpers import context_by_name, ensure_dir, ensure_placeholder
from .structure_sections import (
    create_context_api_files,
    create_domain_files,
    create_infrastructure_structure,
    create_repository_implementations,
    create_use_case_files,
)


def create_modular_monolith_structure(modules_root: str, contexts):
    if not os.path.isdir(modules_root):
        return

    ensure_dir(modules_root, "Shared/Kernel")
    ensure_placeholder(modules_root, "Shared/Kernel", "ModuleKernel.cs", "Shared kernel placeholder")

    context_list = contexts or []
    module_names = [context.name for context in context_list] or ["ExampleModule"]

    for name in module_names:
        module_root = f"Modules/{name}"
        selected_context = context_by_name(context_list, name)

        ensure_dir(modules_root, f"{module_root}/API")
        ensure_dir(modules_root, f"{module_root}/Application")
        ensure_dir(modules_root, f"{module_root}/Domain")
        ensure_dir(modules_root, f"{module_root}/Infrastructure")

        ensure_dir(modules_root, f"{module_root}/API/Controllers")
        ensure_dir(modules_root, f"{module_root}/API/Dtos")
        create_context_api_files(modules_root, [selected_context], root_prefix=f"{module_root}/API")

        ensure_dir(modules_root, f"{module_root}/Application/UseCases")
        ensure_dir(modules_root, f"{module_root}/Domain/Entities")
        ensure_dir(modules_root, f"{module_root}/Domain/Repositories")
        ensure_dir(modules_root, f"{module_root}/Infrastructure/Persistence")

        create_use_case_files(modules_root, [selected_context], root_prefix=f"{module_root}/Application")
        create_domain_files(modules_root, [selected_context], root_prefix=f"{module_root}/Domain")
        ensure_placeholder(modules_root, f"{module_root}/Infrastructure/Persistence", "DatabaseOptions.cs", "Module persistence options")
        create_repository_implementations(modules_root, [selected_context], root_prefix=f"{module_root}/Infrastructure")


def create_microservices_structure(services_root: str, gateway_root: str, shared_root: str, infra_root: str, contexts):
    if os.path.isdir(gateway_root):
        ensure_dir(gateway_root, "Controllers")
        ensure_dir(gateway_root, "Routes")
        ensure_placeholder(gateway_root, "Controllers", "GatewayController.cs", "Gateway controller")
        ensure_placeholder(gateway_root, "Routes", "Routes.cs", "Gateway route definitions")

    if os.path.isdir(shared_root):
        ensure_dir(shared_root, "Contracts")
        ensure_dir(shared_root, "Dtos")
        ensure_placeholder(shared_root, "Contracts", "SharedContracts.cs", "Shared contracts")
        ensure_placeholder(shared_root, "Dtos", "SharedDtos.cs", "Shared DTOs")

    if os.path.isdir(infra_root):
        create_infrastructure_structure(infra_root, contexts)

    if not os.path.isdir(services_root):
        return

    context_list = contexts or []
    service_names = [context.name for context in context_list] or ["ExampleService"]

    for name in service_names:
        service_root = f"Services/{name}"
        selected_context = context_by_name(context_list, name)

        ensure_dir(services_root, f"{service_root}/API/Controllers")
        ensure_dir(services_root, f"{service_root}/API/Dtos")
        ensure_dir(services_root, f"{service_root}/Application/UseCases")
        ensure_dir(services_root, f"{service_root}/Domain/Entities")
        ensure_dir(services_root, f"{service_root}/Domain/Repositories")
        ensure_dir(services_root, f"{service_root}/Infrastructure/Persistence")

        create_context_api_files(services_root, [selected_context], root_prefix=f"{service_root}/API")
        create_use_case_files(services_root, [selected_context], root_prefix=f"{service_root}/Application")
        create_domain_files(services_root, [selected_context], root_prefix=f"{service_root}/Domain")
        ensure_placeholder(services_root, f"{service_root}/Infrastructure/Persistence", "DatabaseOptions.cs", "Service persistence options")
        create_repository_implementations(services_root, [selected_context], root_prefix=f"{service_root}/Infrastructure")