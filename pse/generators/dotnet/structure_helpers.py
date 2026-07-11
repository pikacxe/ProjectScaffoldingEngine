import os

from .template_loader import render_template


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
        },
    )

    with open(path, "w", encoding="utf-8") as f:
        f.write(content)


def remove_placeholder(root: str, folder: str, filename: str):
    path = os.path.join(root, folder, filename)
    if os.path.exists(path):
        os.remove(path)


def context_by_name(contexts, name: str):
    for context in contexts or []:
        if context.name == name:
            return context

    return None


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
        return "    // No properties defined.\n", False

    lines = []
    needs_system = False

    for prop_name, prop_type in properties.items():
        cs_type, requires_system = map_type(prop_type)
        needs_system = needs_system or requires_system
        if cs_type == "string":
            lines.append(f"    public {cs_type} {prop_name} {{ get; set; }} = string.Empty;\n")
        else:
            lines.append(f"    public {cs_type} {prop_name} {{ get; set; }}\n")

    return "".join(lines), needs_system


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


def pick_id_property_name(properties):
    if not properties:
        return "Id"

    for prop_name in properties.keys():
        if prop_name.lower() == "id":
            return prop_name

    return next(iter(properties.keys()))
