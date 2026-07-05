import os

from .template_loader import render_template
from .structure_helpers import build_namespace, build_properties, pick_id_type


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


def write_repository_class(path: str, folder: str, name: str, interface_name: str):
    namespace = build_namespace(path, folder)
    domain_namespace = namespace.replace(".Infrastructure", ".Domain")
    using_line = f"using {domain_namespace};\n"

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
        },
    )

    with open(path, "w", encoding="utf-8") as f:
        f.write(content)


def write_controller(path: str, folder: str, name: str, entity, dto_name: str):
    if os.path.exists(path):
        return

    namespace = build_namespace(path, folder)
    id_type = pick_id_type(entity.properties)
    methods = render_template(
        "ControllerMethods.cs.tmpl",
        {
            "DtoType": dto_name,
            "IdType": id_type,
        },
    )

    content = render_template(
        "Controller.cs.tmpl",
        {
            "UsingLines": "using System.Collections.Generic;\n\n",
            "Namespace": namespace,
            "ControllerName": name,
            "Methods": methods,
        },
    )

    with open(path, "w", encoding="utf-8") as f:
        f.write(content)