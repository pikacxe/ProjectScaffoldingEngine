import os

from .template_loader import render_template
from .structure_helpers import build_namespace, build_properties, map_type, pick_id_property_name, pick_id_type


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
        },
    )

    with open(path, "w", encoding="utf-8") as f:
        f.write(content)


def write_repository_class(path: str, folder: str, name: str, interface_name: str, entity_name: str, id_type: str, id_property_name: str):
    namespace = build_namespace(path, folder)
    domain_namespace = namespace.replace(".Infrastructure.Repositories", ".Domain")

    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            content = f.read()

        if (
            "GetAll()" in content
            and "GetById(" in content
            and "Create(" in content
            and "NotImplementedException" not in content
            and "Array.Empty" not in content
            and "{{" not in content
            and "Repositories.Entities" not in content
            and "Repositories.Repositories" not in content
        ):
            return

    content = render_template(
        "RepositoryImplementation.cs.tmpl",
        {
            "DomainNamespace": domain_namespace,
            "EntityName": entity_name,
            "IdType": id_type,
            "IdPropertyName": id_property_name,
            "Namespace": namespace,
            "ClassName": name,
            "InterfaceName": interface_name,
        },
    )

    with open(path, "w", encoding="utf-8") as f:
        f.write(content)


def write_service_interface(path: str, folder: str, name: str, entity_name: str, id_type: str):
    namespace = build_namespace(path, folder)
    domain_namespace = namespace.replace(".Application.Interfaces", ".Domain")

    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            content = f.read()

        if (
            "GetAll()" in content
            and "GetById(" in content
            and "Create(" in content
            and "bool Update(" in content
            and "bool Delete(" in content
            and "{{" not in content
        ):
            return

    content = render_template(
        "ApplicationServiceInterface.cs.tmpl",
        {
            "DomainNamespace": domain_namespace,
            "Namespace": namespace,
            "InterfaceName": name,
            "EntityName": entity_name,
            "IdType": id_type,
        },
    )

    with open(path, "w", encoding="utf-8") as f:
        f.write(content)


def write_service_class(path: str, folder: str, name: str, interface_name: str, entity_name: str, id_type: str, id_property_name: str):
    namespace = build_namespace(path, folder)
    domain_namespace = namespace.replace(".Application.Services", ".Domain")
    interface_namespace = namespace.replace(".Services", ".Interfaces")

    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            content = f.read()

        if (
            "GetAll()" in content
            and "GetById(" in content
            and "Create(" in content
            and "bool Update(" in content
            and "bool Delete(" in content
            and "{{" not in content
            and "TODO" not in content
        ):
            return

    content = render_template(
        "ApplicationService.cs.tmpl",
        {
            "DomainNamespace": domain_namespace,
            "InterfaceNamespace": interface_namespace,
            "Namespace": namespace,
            "ClassName": name,
            "InterfaceName": interface_name,
            "EntityName": entity_name,
            "IdType": id_type,
            "IdPropertyName": id_property_name,
        },
    )

    with open(path, "w", encoding="utf-8") as f:
        f.write(content)


def write_repository_interface(path: str, folder: str, name: str, entity_name: str, id_type: str):
    namespace = build_namespace(path, folder)
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            content = f.read()

        if (
            "GetAll()" in content
            and "GetById(" in content
            and "Create(" in content
            and "{{" not in content
        ):
            return

    content = render_template(
        "RepositoryInterface.cs.tmpl",
        {
            "DomainNamespace": namespace.replace(".Repositories", ""),
            "Namespace": namespace,
            "InterfaceName": name,
            "EntityName": entity_name,
            "IdType": id_type,
        },
    )

    with open(path, "w", encoding="utf-8") as f:
        f.write(content)


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


def write_mediatr_cqrs_class(path: str, folder: str, entity_name: str, id_type: str):
    write_cqrs_class(path, folder, entity_name, id_type, "MediatRRequests.cs.tmpl")


def write_wolverine_cqrs_class(path: str, folder: str, entity_name: str, id_type: str):
    write_cqrs_class(path, folder, entity_name, id_type, "WolverineMessages.cs.tmpl")


def write_cqrs_class(path: str, folder: str, entity_name: str, id_type: str, template_name: str):
    namespace = build_namespace(path, folder)
    project_root = namespace.split(".")[0]

    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            content = f.read()

        if "Handler" in content and "{{" not in content and "TODO" not in content:
            return

    content = render_template(
        template_name,
        {
            "Namespace": namespace,
            "DomainNamespace": f"{project_root}.Domain",
            "InterfaceNamespace": f"{project_root}.Application.Interfaces",
            "EntityName": entity_name,
            "IdType": id_type,
        },
    )

    with open(path, "w", encoding="utf-8") as f:
        f.write(content)


def write_controller(path: str, folder: str, name: str, entity, dto_name: str, use_mapping: bool = False, cqrs_implementation: str = None):
    namespace = build_namespace(path, folder)
    entity_namespace = namespace.replace(".API.Controllers", ".Domain.Entities").replace(".Presentation.Controllers", ".Domain.Entities").replace(".Gateway.Controllers", ".Domain.Entities")
    service_namespace = namespace.replace(".API.Controllers", ".Application.Interfaces").replace(".Presentation.Controllers", ".Application.Interfaces").replace(".Gateway.Controllers", ".Application.Interfaces")
    cqrs_namespace = namespace.replace(".API.Controllers", ".Application.Cqrs").replace(".Presentation.Controllers", ".Application.Cqrs").replace(".Gateway.Controllers", ".Application.Cqrs")
    dto_namespace = build_namespace(path, "Dtos")
    id_type = pick_id_type(entity.properties)
    id_property_name = pick_id_property_name(entity.properties)
    cqrs_implementation = (cqrs_implementation or "").lower()

    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            content = f.read()

        if (
            "private readonly" in content
            and "{{" not in content
            and "TODO" not in content
            and (
                use_mapping
                or ("ToDto(" in content and "ToEntity(" in content)
            )
            and (
                (cqrs_implementation == "mediatr" and "IMediator" in content)
                or (cqrs_implementation == "wolverine" and "IMessageBus" in content)
                or (cqrs_implementation not in {"mediatr", "wolverine"} and f"I{entity.name}Service" in content)
            )
        ):
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

    using_lines = (
        "using System.Collections.Generic;\n"
        "using System.Linq;\n"
        "using System.Threading.Tasks;\n"
        f"using {dto_namespace};\n"
        f"using {entity_namespace};\n"
    )
    if cqrs_implementation in {"mediatr", "wolverine"}:
        using_lines += f"using {cqrs_namespace};\n"
    else:
        using_lines += f"using {service_namespace};\n"

    if cqrs_implementation == "mediatr":
        using_lines += "using MediatR;\n"
    elif cqrs_implementation == "wolverine":
        using_lines += "using Wolverine;\n"

    if use_mapping:
        using_lines += "using Mapster;\n"

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


def build_controller_methods(entity_name: str, dto_name: str, id_type: str, id_property_name: str, properties, use_mapping: bool = False, cqrs_implementation: str = None):
    if cqrs_implementation == "mediatr":
        return build_mediatr_controller_methods(entity_name, dto_name, id_type, id_property_name, properties, use_mapping)

    if cqrs_implementation == "wolverine":
        return build_wolverine_controller_methods(entity_name, dto_name, id_type, id_property_name, properties, use_mapping)

    service_field_name = f"_{entity_name[0].lower()}{entity_name[1:]}Service"
    service_parameter_name = f"{entity_name[0].lower()}{entity_name[1:]}Service"
    service_interface_name = f"I{entity_name}Service"

    core_methods = (
        f"    private readonly {service_interface_name} {service_field_name};\n\n"
        f"    public {entity_name}Controller({service_interface_name} {service_parameter_name})\n"
        "    {\n"
        f"        {service_field_name} = {service_parameter_name};\n"
        "    }\n\n"
        "    [HttpGet]\n"
        f"    public ActionResult<List<{dto_name}>> GetAll()\n"
        "    {\n"
        f"        var entities = {service_field_name}.GetAll().Select(entity => {map_expression('entity', dto_name, use_mapping)}).ToList();\n"
        "        return Ok(entities);\n"
        "    }\n\n"
        "    [HttpGet(\"{id}\")]\n"
        f"    public ActionResult<{dto_name}> GetById({id_type} id)\n"
        "    {\n"
        f"        var entity = {service_field_name}.GetById(id);\n"
        "        if (entity is null)\n"
        "        {\n"
        "            return NotFound();\n"
        "        }\n\n"
        f"        return Ok({map_expression('entity', dto_name, use_mapping)});\n"
        "    }\n\n"
        "    [HttpPost]\n"
        f"    public ActionResult<{dto_name}> Create({dto_name} request)\n"
        "    {\n"
        f"        var entity = {map_expression('request', entity_name, use_mapping)};\n"
        f"        var created = {service_field_name}.Create(entity);\n"
        f"        return CreatedAtAction(nameof(GetById), new {{ id = created.{id_property_name} }}, {map_expression('created', dto_name, use_mapping)});\n"
        "    }\n\n"
        "    [HttpPut(\"{id}\")]\n"
        f"    public IActionResult Update({id_type} id, {dto_name} request)\n"
        "    {\n"
        f"        var entity = {map_expression('request', entity_name, use_mapping)};\n"
        f"        if (!{service_field_name}.Update(id, entity))\n"
        "        {\n"
        "            return NotFound();\n"
        "        }\n\n"
        "        return NoContent();\n"
        "    }\n\n"
        "    [HttpDelete(\"{id}\")]\n"
        f"    public IActionResult Delete({id_type} id)\n"
        "    {\n"
        f"        if (!{service_field_name}.Delete(id))\n"
        "        {\n"
        "            return NotFound();\n"
        "        }\n\n"
        "        return NoContent();\n"
        "    }\n"
    )

    if use_mapping:
        return core_methods

    return core_methods + build_manual_mapping_methods(entity_name, dto_name, properties)


def build_mediatr_controller_methods(entity_name: str, dto_name: str, id_type: str, id_property_name: str, properties, use_mapping: bool = False):
    core_methods = (
        "    private readonly IMediator _mediator;\n\n"
        f"    public {entity_name}Controller(IMediator mediator)\n"
        "    {\n"
        "        _mediator = mediator;\n"
        "    }\n\n"
        "    [HttpGet]\n"
        f"    public async Task<ActionResult<List<{dto_name}>>> GetAll()\n"
        "    {\n"
        f"        var entities = await _mediator.Send(new GetAll{entity_name}Query());\n"
        f"        var response = entities.Select(entity => {map_expression('entity', dto_name, use_mapping)}).ToList();\n"
        "        return Ok(response);\n"
        "    }\n\n"
        "    [HttpGet(\"{id}\")]\n"
        f"    public async Task<ActionResult<{dto_name}>> GetById({id_type} id)\n"
        "    {\n"
        f"        var entity = await _mediator.Send(new Get{entity_name}ByIdQuery(id));\n"
        "        if (entity is null)\n"
        "        {\n"
        "            return NotFound();\n"
        "        }\n\n"
        f"        return Ok({map_expression('entity', dto_name, use_mapping)});\n"
        "    }\n\n"
        "    [HttpPost]\n"
        f"    public async Task<ActionResult<{dto_name}>> Create({dto_name} request)\n"
        "    {\n"
        f"        var entity = {map_expression('request', entity_name, use_mapping)};\n"
        f"        var created = await _mediator.Send(new Create{entity_name}Command(entity));\n"
        f"        return CreatedAtAction(nameof(GetById), new {{ id = created.{id_property_name} }}, {map_expression('created', dto_name, use_mapping)});\n"
        "    }\n\n"
        "    [HttpPut(\"{id}\")]\n"
        f"    public async Task<IActionResult> Update({id_type} id, {dto_name} request)\n"
        "    {\n"
        f"        var entity = {map_expression('request', entity_name, use_mapping)};\n"
        f"        var updated = await _mediator.Send(new Update{entity_name}Command(id, entity));\n"
        "        if (!updated)\n"
        "        {\n"
        "            return NotFound();\n"
        "        }\n\n"
        "        return NoContent();\n"
        "    }\n\n"
        "    [HttpDelete(\"{id}\")]\n"
        f"    public async Task<IActionResult> Delete({id_type} id)\n"
        "    {\n"
        f"        var deleted = await _mediator.Send(new Delete{entity_name}Command(id));\n"
        "        if (!deleted)\n"
        "        {\n"
        "            return NotFound();\n"
        "        }\n\n"
        "        return NoContent();\n"
        "    }\n"
    )

    if use_mapping:
        return core_methods

    return core_methods + build_manual_mapping_methods(entity_name, dto_name, properties)


def build_wolverine_controller_methods(entity_name: str, dto_name: str, id_type: str, id_property_name: str, properties, use_mapping: bool = False):
    core_methods = (
        "    private readonly IMessageBus _messageBus;\n\n"
        f"    public {entity_name}Controller(IMessageBus messageBus)\n"
        "    {\n"
        "        _messageBus = messageBus;\n"
        "    }\n\n"
        "    [HttpGet]\n"
        f"    public async Task<ActionResult<List<{dto_name}>>> GetAll()\n"
        "    {\n"
        f"        var entities = await _messageBus.InvokeAsync<IEnumerable<{entity_name}>>(new GetAll{entity_name}Query());\n"
        f"        var response = entities.Select(entity => {map_expression('entity', dto_name, use_mapping)}).ToList();\n"
        "        return Ok(response);\n"
        "    }\n\n"
        "    [HttpGet(\"{id}\")]\n"
        f"    public async Task<ActionResult<{dto_name}>> GetById({id_type} id)\n"
        "    {\n"
        f"        var entity = await _messageBus.InvokeAsync<{entity_name}?>(new Get{entity_name}ByIdQuery(id));\n"
        "        if (entity is null)\n"
        "        {\n"
        "            return NotFound();\n"
        "        }\n\n"
        f"        return Ok({map_expression('entity', dto_name, use_mapping)});\n"
        "    }\n\n"
        "    [HttpPost]\n"
        f"    public async Task<ActionResult<{dto_name}>> Create({dto_name} request)\n"
        "    {\n"
        f"        var entity = {map_expression('request', entity_name, use_mapping)};\n"
        f"        var created = await _messageBus.InvokeAsync<{entity_name}>(new Create{entity_name}Command(entity));\n"
        f"        return CreatedAtAction(nameof(GetById), new {{ id = created.{id_property_name} }}, {map_expression('created', dto_name, use_mapping)});\n"
        "    }\n\n"
        "    [HttpPut(\"{id}\")]\n"
        f"    public async Task<IActionResult> Update({id_type} id, {dto_name} request)\n"
        "    {\n"
        f"        var entity = {map_expression('request', entity_name, use_mapping)};\n"
        f"        var updated = await _messageBus.InvokeAsync<bool>(new Update{entity_name}Command(id, entity));\n"
        "        if (!updated)\n"
        "        {\n"
        "            return NotFound();\n"
        "        }\n\n"
        "        return NoContent();\n"
        "    }\n\n"
        "    [HttpDelete(\"{id}\")]\n"
        f"    public async Task<IActionResult> Delete({id_type} id)\n"
        "    {\n"
        f"        var deleted = await _messageBus.InvokeAsync<bool>(new Delete{entity_name}Command(id));\n"
        "        if (!deleted)\n"
        "        {\n"
        "            return NotFound();\n"
        "        }\n\n"
        "        return NoContent();\n"
        "    }\n"
    )

    if use_mapping:
        return core_methods

    return core_methods + build_manual_mapping_methods(entity_name, dto_name, properties)


def build_manual_mapping_methods(entity_name: str, dto_name: str, properties):
    to_dto_assignments = build_object_initializer("entity", dto_name, properties)
    to_entity_assignments = build_object_initializer("dto", entity_name, properties)

    return (
        "\n"
        f"    private static {dto_name} ToDto({entity_name} entity)\n"
        "    {\n"
        f"        return new {dto_name}\n"
        "        {\n"
        f"{to_dto_assignments}"
        "        };\n"
        "    }\n\n"
        f"    private static {entity_name} ToEntity({dto_name} dto)\n"
        "    {\n"
        f"        return new {entity_name}\n"
        "        {\n"
        f"{to_entity_assignments}"
        "        };\n"
        "    }\n"
    )


def map_expression(source_name: str, target_name: str, use_mapping: bool):
    if use_mapping:
        return f"{source_name}.Adapt<{target_name}>()"

    if target_name.endswith("Dto"):
        return f"ToDto({source_name})"

    return f"ToEntity({source_name})"


def build_object_initializer(source_name: str, target_name: str, properties):
    if not properties:
        return ""

    lines = []
    for prop_name in properties:
        lines.append(f"            {prop_name} = {source_name}.{prop_name},\n")

    return "".join(lines)


def write_test_class(path: str, folder: str, name: str, entity):
    namespace = build_namespace(path, folder)
    project_root = namespace.split(".")[0]
    subject_name = entity.name
    body = build_entity_test_body(entity)
    content = render_template(
        "TestClass.cs.tmpl",
        {
            "UsingLines": f"using System;\nusing {project_root}.Domain.Entities;\n",
            "Namespace": namespace,
            "ClassName": name,
            "TestMethodName": f"CanCreate{subject_name}",
            "Body": body,
        },
    )

    with open(path, "w", encoding="utf-8") as f:
        f.write(content)


def build_entity_test_body(entity):
    assignments = []
    assertions = []

    for prop_name, prop_type in (entity.properties or {}).items():
        cs_type, _ = map_type(prop_type)
        value = sample_value(prop_name, cs_type)
        assignments.append(f"            {prop_name} = {value},\n")
        assertions.append(assertion_for_property(prop_name, cs_type, value))

    if not assignments:
        return f"        var entity = new {entity.name}();\n\n        Assert.NotNull(entity);\n"

    return (
        f"        var entity = new {entity.name}\n"
        "        {\n"
        f"{''.join(assignments)}"
        "        };\n\n"
        f"{''.join(assertions)}"
    )


def sample_value(prop_name: str, cs_type: str):
    if cs_type == "Guid":
        return "Guid.NewGuid()"
    if cs_type == "DateTime":
        return "DateTime.UtcNow"
    if cs_type == "string":
        return f"\"{prop_name}\""
    if cs_type == "bool":
        return "true"
    if cs_type in {"int", "long"}:
        return "1"
    if cs_type == "decimal":
        return "1m"
    if cs_type == "double":
        return "1d"
    if cs_type == "float":
        return "1f"

    return f"new {cs_type}()"


def assertion_for_property(prop_name: str, cs_type: str, value: str):
    if cs_type == "Guid":
        return f"        Assert.NotEqual(Guid.Empty, entity.{prop_name});\n"
    if cs_type == "DateTime":
        return f"        Assert.NotEqual(default, entity.{prop_name});\n"
    if cs_type == "string":
        return f"        Assert.Equal({value}, entity.{prop_name});\n"
    if cs_type == "bool":
        return f"        Assert.True(entity.{prop_name});\n"

    return f"        Assert.Equal({value}, entity.{prop_name});\n"
