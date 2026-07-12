from ..structure_helpers import build_namespace, map_type
from ..template_loader import render_template


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
