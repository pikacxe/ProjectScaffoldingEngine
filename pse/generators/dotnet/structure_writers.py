import os

from .template_loader import render_template
from .structure_helpers import build_namespace, build_properties, pick_id_property_name, pick_id_type


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


def write_repository_class(path: str, folder: str, name: str, interface_name: str, entity_name: str, id_type: str):
    namespace = build_namespace(path, folder)
    domain_namespace = namespace.replace(".Infrastructure.Repositories", ".Domain")

    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            content = f.read()

        if (
            "GetAll()" in content
            and "GetById(" in content
            and "Create(" in content
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
            "Namespace": namespace,
            "ClassName": name,
            "InterfaceName": interface_name,
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


def write_controller(path: str, folder: str, name: str, entity, dto_name: str):
    namespace = build_namespace(path, folder)
    entity_namespace = namespace.replace(".API.Controllers", ".Domain.Entities").replace(".Presentation.Controllers", ".Domain.Entities").replace(".Gateway.Controllers", ".Domain.Entities")
    repository_namespace = namespace.replace(".API.Controllers", ".Domain.Repositories").replace(".Presentation.Controllers", ".Domain.Repositories").replace(".Gateway.Controllers", ".Domain.Repositories")
    dto_namespace = build_namespace(path, "Dtos")
    id_type = pick_id_type(entity.properties)
    id_property_name = pick_id_property_name(entity.properties)

    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            content = f.read()

        if (
            "private readonly" in content
            and "ToDto(" in content
            and "ToEntity(" in content
            and "{{" not in content
        ):
            return

    methods = build_controller_methods(
        entity_name=entity.name,
        dto_name=dto_name,
        id_type=id_type,
        id_property_name=id_property_name,
        properties=list(entity.properties.keys()),
    )

    content = render_template(
        "Controller.cs.tmpl",
        {
            "UsingLines": (
                "using System.Collections.Generic;\n"
                "using System.Linq;\n"
                f"using {dto_namespace};\n"
                f"using {entity_namespace};\n"
                f"using {repository_namespace};\n\n"
            ),
            "Namespace": namespace,
            "ControllerName": name,
            "Methods": methods,
        },
    )

    with open(path, "w", encoding="utf-8") as f:
        f.write(content)


def build_controller_methods(entity_name: str, dto_name: str, id_type: str, id_property_name: str, properties):
    repository_field_name = f"_{entity_name[0].lower()}{entity_name[1:]}Repository"
    repository_parameter_name = f"{entity_name[0].lower()}{entity_name[1:]}Repository"
    repository_interface_name = f"I{entity_name}Repository"

    to_dto_assignments = build_object_initializer("entity", dto_name, properties)
    to_entity_assignments = build_object_initializer("dto", entity_name, properties)

    return (
        f"    private readonly {repository_interface_name} {repository_field_name};\n\n"
        f"    public {entity_name}Controller({repository_interface_name} {repository_parameter_name})\n"
        "    {\n"
        f"        {repository_field_name} = {repository_parameter_name};\n"
        "    }\n\n"
        "    [HttpGet]\n"
        f"    public ActionResult<List<{dto_name}>> GetAll()\n"
        "    {\n"
        f"        var entities = {repository_field_name}.GetAll().Select(ToDto).ToList();\n"
        "        return Ok(entities);\n"
        "    }\n\n"
        "    [HttpGet(\"{id}\")]\n"
        f"    public ActionResult<{dto_name}> GetById({id_type} id)\n"
        "    {\n"
        f"        var entity = {repository_field_name}.GetById(id);\n"
        "        if (entity is null)\n"
        "        {\n"
        "            return NotFound();\n"
        "        }\n\n"
        "        return Ok(ToDto(entity));\n"
        "    }\n\n"
        "    [HttpPost]\n"
        f"    public ActionResult<{dto_name}> Create({dto_name} request)\n"
        "    {\n"
        f"        var entity = ToEntity(request);\n"
        f"        {repository_field_name}.Create(entity);\n"
        f"        return CreatedAtAction(nameof(GetById), new {{ id = entity.{id_property_name} }}, ToDto(entity));\n"
        "    }\n\n"
        "    [HttpPut(\"{id}\")]\n"
        f"    public IActionResult Update({id_type} id, {dto_name} request)\n"
        "    {\n"
        f"        var entity = ToEntity(request);\n"
        f"        entity.{id_property_name} = id;\n"
        f"        {repository_field_name}.Update(entity);\n"
        "        return NoContent();\n"
        "    }\n\n"
        "    [HttpDelete(\"{id}\")]\n"
        f"    public IActionResult Delete({id_type} id)\n"
        "    {\n"
        f"        var existingEntity = {repository_field_name}.GetById(id);\n"
        "        if (existingEntity is null)\n"
        "        {\n"
        "            return NotFound();\n"
        "        }\n\n"
        f"        {repository_field_name}.Delete(id);\n"
        "        return NoContent();\n"
        "    }\n\n"
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


def build_object_initializer(source_name: str, target_name: str, properties):
    if not properties:
        return ""

    lines = []
    for prop_name in properties:
        lines.append(f"            {prop_name} = {source_name}.{prop_name},\n")

    return "".join(lines)


def write_test_class(path: str, folder: str, name: str, subject_name: str):
    namespace = build_namespace(path, folder)
    content = render_template(
        "TestClass.cs.tmpl",
        {
            "Namespace": namespace,
            "ClassName": name,
            "TestMethodName": f"CanCreate{subject_name}",
        },
    )

    with open(path, "w", encoding="utf-8") as f:
        f.write(content)