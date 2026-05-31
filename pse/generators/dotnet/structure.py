import os

from .template_loader import render_template


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
            contexts
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
    ensure_placeholder(infra_root, "Persistence", "DatabaseOptions.cs", "Infrastructure persistence options")
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


def create_modular_monolith_structure(modules_root: str, contexts):
    if not os.path.isdir(modules_root):
        return

    ensure_dir(modules_root, "Shared/Kernel")
    ensure_placeholder(modules_root, "Shared/Kernel", "ModuleKernel.cs", "Shared kernel placeholder")

    if not contexts:
        contexts = []

    module_names = [c.name for c in contexts] or ["ExampleModule"]

    for name in module_names:
        module_root = f"Modules/{name}"
        ensure_dir(modules_root, f"{module_root}/API")
        ensure_dir(modules_root, f"{module_root}/Application")
        ensure_dir(modules_root, f"{module_root}/Domain")
        ensure_dir(modules_root, f"{module_root}/Infrastructure")

        ensure_dir(modules_root, f"{module_root}/API/Controllers")
        ensure_dir(modules_root, f"{module_root}/API/Dtos")
        create_context_api_files(modules_root, [context_by_name(contexts, name)], root_prefix=f"{module_root}/API")

        ensure_dir(modules_root, f"{module_root}/Application/UseCases")
        ensure_dir(modules_root, f"{module_root}/Domain/Entities")
        ensure_dir(modules_root, f"{module_root}/Domain/Repositories")
        ensure_dir(modules_root, f"{module_root}/Infrastructure/Persistence")

        create_use_case_files(modules_root, [context_by_name(contexts, name)], root_prefix=f"{module_root}/Application")
        create_domain_files(modules_root, [context_by_name(contexts, name)], root_prefix=f"{module_root}/Domain")
        ensure_placeholder(modules_root, f"{module_root}/Infrastructure/Persistence", "DatabaseOptions.cs", "Module persistence options")
        create_repository_implementations(modules_root, [context_by_name(contexts, name)], root_prefix=f"{module_root}/Infrastructure")


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

    if not contexts:
        contexts = []

    service_names = [c.name for c in contexts] or ["ExampleService"]

    for name in service_names:
        service_root = f"Services/{name}"
        ensure_dir(services_root, f"{service_root}/API/Controllers")
        ensure_dir(services_root, f"{service_root}/API/Dtos")
        ensure_dir(services_root, f"{service_root}/Application/UseCases")
        ensure_dir(services_root, f"{service_root}/Domain/Entities")
        ensure_dir(services_root, f"{service_root}/Domain/Repositories")
        ensure_dir(services_root, f"{service_root}/Infrastructure/Persistence")

        create_context_api_files(services_root, [context_by_name(contexts, name)], root_prefix=f"{service_root}/API")
        create_use_case_files(services_root, [context_by_name(contexts, name)], root_prefix=f"{service_root}/Application")
        create_domain_files(services_root, [context_by_name(contexts, name)], root_prefix=f"{service_root}/Domain")
        ensure_placeholder(services_root, f"{service_root}/Infrastructure/Persistence", "DatabaseOptions.cs", "Service persistence options")
        create_repository_implementations(services_root, [context_by_name(contexts, name)], root_prefix=f"{service_root}/Infrastructure")


def ensure_dir(root: str, name: str):
    path = os.path.join(root, name)
    os.makedirs(path, exist_ok=True)


def ensure_placeholder(root: str, folder: str, filename: str, description: str):
    path = os.path.join(root, folder, filename)
    if os.path.exists(path):
        return

    class_name = os.path.splitext(filename)[0]
    namespace = build_namespace(path, folder)

    content = render_template(
        "CSharpClass.cs.tmpl",
        {
            "UsingLines": "",
            "Namespace": namespace,
            "Signature": f"public class {class_name}",
            "Body": f"    // {description}.\n",
        }
    )

    with open(path, "w", encoding="utf-8") as f:
        f.write(content)


def remove_placeholder(root: str, folder: str, filename: str):
    path = os.path.join(root, folder, filename)
    if os.path.exists(path):
        os.remove(path)


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
            write_csharp_class(repo_path, "Repositories", repo_name, is_interface=True)
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
            write_repository_class(repo_path, "Repositories", repo_name, interface_name)
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
            write_csharp_class(test_path, "Unit", test_name)
            created = True

    return created


def context_by_name(contexts, name: str):
    for context in contexts or []:
        if context.name == name:
            return context

    return None


def write_csharp_class(path: str, folder: str, name: str, base_type: str = None, properties=None, is_interface: bool = False):
    if os.path.exists(path):
        return

    namespace = build_namespace(path, folder)
    prop_lines, needs_system = build_properties(properties or {})
    using_lines = "using System;\n\n" if needs_system else ""

    if is_interface:
        signature = f"public interface {name}"
    else:
        signature = f"public class {name}"
        if base_type:
            signature += f" : {base_type}"

    content = render_template(
        "CSharpClass.cs.tmpl",
        {
            "UsingLines": using_lines,
            "Namespace": namespace,
            "Signature": signature,
            "Body": prop_lines,
        }
    )

    with open(path, "w", encoding="utf-8") as f:
        f.write(content)


def write_repository_class(path: str, folder: str, name: str, interface_name: str):
    namespace = build_namespace(path, folder)
    domain_namespace = namespace.replace(".Infrastructure", ".Domain")
    using_line = f"using {domain_namespace}.Repositories;\n"

    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            content = f.read()

        if using_line not in content:
            content = using_line + "\n" + content.lstrip()

            with open(path, "w", encoding="utf-8") as f:
                f.write(content)
        return

    content = render_template(
        "Repository.cs.tmpl",
        {
            "DomainNamespace": domain_namespace,
            "Namespace": namespace,
            "ClassName": name,
            "InterfaceName": interface_name,
        }
    )

    with open(path, "w", encoding="utf-8") as f:
        f.write(content)


def write_controller(path: str, folder: str, name: str, entity, dto_name: str):
    if os.path.exists(path):
        return

    namespace = build_namespace(path, folder)
    id_type = pick_id_type(entity.properties)
    dto_type = dto_name

    methods = build_controller_methods(dto_type, id_type)
    content = render_template(
        "Controller.cs.tmpl",
        {
            "UsingLines": "using System.Collections.Generic;\n\n",
            "Namespace": namespace,
            "ControllerName": name,
            "Methods": methods,
        }
    )

    with open(path, "w", encoding="utf-8") as f:
        f.write(content)


def build_namespace(path: str, folder: str):
    root_name = find_project_root_name(path)
    folder_ns = folder.replace("/", ".").replace(os.sep, ".")
    return f"{root_name}.{folder_ns}"


def find_project_root_name(path: str):
    current = os.path.dirname(path)

    while current and current != os.path.dirname(current):
        name = os.path.basename(current)
        if "." in name:
            return name.replace("-", "_")
        current = os.path.dirname(current)

    return os.path.basename(os.path.dirname(path)).replace("-", "_")


def build_properties(properties):
    if not properties:
        return "    // TODO: add properties.\n", False

    lines = []
    needs_system = False

    for prop_name, prop_type in properties.items():
        cs_type, requires_system = map_type(prop_type)
        needs_system = needs_system or requires_system
        lines.append(f"    public {cs_type} {prop_name} {{ get; set; }}\n")

    return "".join(lines), needs_system


def build_controller_methods(dto_type: str, id_type: str):
    return (
        f"    [HttpGet]\n"
        f"    public ActionResult<List<{dto_type}>> GetAll()\n"
        "    {\n"
        f"        return Ok(new List<{dto_type}>());\n"
        "    }\n\n"
        f"    [HttpGet(\"{{id}}\")]\n"
        f"    public ActionResult<{dto_type}> GetById({id_type} id)\n"
        "    {\n"
        f"        return Ok(new {dto_type}());\n"
        "    }\n\n"
        f"    [HttpPost]\n"
        f"    public ActionResult<{dto_type}> Create({dto_type} request)\n"
        "    {\n"
        "        return CreatedAtAction(nameof(GetById), new { id = request.Id }, request);\n"
        "    }\n"
    )


def map_type(type_name: str):
    if not type_name:
        return "string", False

    lookup = {
        "guid": "Guid",
        "datetime": "DateTime",
        "string": "string",
        "int": "int",
        "long": "long",
        "bool": "bool",
        "boolean": "bool",
        "decimal": "decimal",
        "double": "double",
        "float": "float",
    }

    key = type_name.lower()
    mapped = lookup.get(key, type_name)
    requires_system = mapped in {"Guid", "DateTime"}
    return mapped, requires_system


def pick_id_type(properties):
    if not properties:
        return "Guid"

    for prop_name, prop_type in properties.items():
        if prop_name.lower() == "id":
            return map_type(prop_type)[0]

    return "Guid"
