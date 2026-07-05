import os

from .structure_archetypes import create_microservices_structure, create_modular_monolith_structure
from .structure_sections import (
    create_application_structure,
    create_api_structure,
    create_domain_structure,
    create_infrastructure_structure,
    create_presentation_structure,
    create_tests_structure,
)


def create_structure(ctx):
    base = ctx.architecture.project.name
    output_dir = os.path.abspath(ctx.output_dir)
    archetype = ctx.architecture.project.archetype
    contexts = ctx.architecture.contexts

    if archetype == "ModularMonolith":
        modules_root = os.path.join(output_dir, f"{base}.Modules")
        create_modular_monolith_structure(modules_root, contexts)
        return

    if archetype == "Microservices":
        services_root = os.path.join(output_dir, f"{base}.Services")
        gateway_root = os.path.join(output_dir, f"{base}.Gateway")
        shared_root = os.path.join(output_dir, f"{base}.Shared")
        infra_root = os.path.join(output_dir, f"{base}.Infrastructure")
        create_microservices_structure(
            services_root,
            gateway_root,
            shared_root,
            infra_root,
            contexts,
        )
        return

    api_root = os.path.join(output_dir, f"{base}.API")
    presentation_root = os.path.join(output_dir, f"{base}.Presentation")
    app_root = os.path.join(output_dir, f"{base}.Application")
    domain_root = os.path.join(output_dir, f"{base}.Domain")
    infra_root = os.path.join(output_dir, f"{base}.Infrastructure")
    tests_root = os.path.join(output_dir, f"{base}.Tests")

    if os.path.isdir(api_root):
        create_api_structure(api_root, contexts)

    if os.path.isdir(presentation_root):
        create_presentation_structure(presentation_root, contexts)

    create_application_structure(app_root, contexts)
    create_domain_structure(domain_root, contexts)
    create_infrastructure_structure(infra_root, contexts)

    if os.path.isdir(tests_root):
        create_tests_structure(tests_root, contexts)
