import os

from ..structure_helpers import build_namespace, build_properties
from ..template_loader import render_template


def write_csharp_class(path: str, folder: str, name: str, base_type: str = None, properties=None, is_interface: bool = False, additional_usings=None):
    if os.path.exists(path):
        return

    namespace = build_namespace(path, folder)
    prop_lines, needs_system = build_properties(properties or {})
    using_names = list(additional_usings or [])
    if needs_system:
        using_names.insert(0, "System")
    using_lines = "".join(f"using {item};\n" for item in dict.fromkeys(using_names))
    if using_lines:
        using_lines += "\n"

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


def write_aggregate_class(path: str, folder: str, aggregate):
    namespace = build_namespace(path, folder)
    project_root = namespace.rsplit(".Aggregates", 1)[0]
    child_properties = "".join(
        f"    public List<{child}> {child}s {{ get; }} = new();\n"
        for child in aggregate.children
    )
    content = render_template(
        "Aggregate.cs.tmpl",
        {
            "EntityNamespace": f"{project_root}.Entities",
            "Namespace": namespace,
            "AggregateName": aggregate.name,
            "RootType": aggregate.root,
            "ChildProperties": child_properties,
        },
    )
    with open(path, "w", encoding="utf-8") as handle:
        handle.write(content)


def write_repository_class(path: str, folder: str, name: str, interface_name: str, entity_name: str, id_type: str, id_property_name: str, use_database: bool = False):
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

    template_name = (
        "EfRepositoryImplementation.cs.tmpl"
        if use_database
        else "RepositoryImplementation.cs.tmpl"
    )
    content = render_template(
        template_name,
        {
            "DomainNamespace": domain_namespace,
            "EntityName": entity_name,
            "IdType": id_type,
            "IdPropertyName": id_property_name,
            "Namespace": namespace,
            "ClassName": name,
            "InterfaceName": interface_name,
            "PersistenceNamespace": namespace.replace(".Repositories", ".Persistence"),
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
