import os

from pse.generators.dotnet.process import run_dotnet


def resolve_packages(ctx):
    if hasattr(ctx, "capabilities") and ctx.capabilities:
        return {k: v.value for k, v in ctx.capabilities.capabilities.items()}

    archetype = ctx.architecture.project.archetype.lower()
    preset = ctx.presets.get(archetype, {})

    return preset.get("capabilities", {})


def capability_project_map():
    return {
        "logging": "API",
        "validation": "API",
        "mapping": "API",
        "cqrs": "Application",
        "database": "Infrastructure",
        "cache": "Infrastructure",
        "messaging": "Infrastructure",
        "testing": "Tests",
    }


def project_path(ctx, layer: str):
    base = ctx.architecture.project.name
    output_dir = os.path.abspath(ctx.output_dir)
    project_name = f"{base}.{layer}"
    return os.path.join(output_dir, project_name, f"{project_name}.csproj")


def first_existing_project(ctx, layers):
    for layer in layers:
        path = project_path(ctx, layer)
        if os.path.exists(path):
            return path

    return None


def configure_packages(ctx):

    packages = resolve_packages(ctx)
    project_map = capability_project_map()
    default_project = project_path(ctx, "Application")

    capability_order = list(packages)
    dependency_graph = getattr(ctx, "dependency_graph", None)
    if dependency_graph:
        ordered = dependency_graph.topological_sort()
        capability_order = [name for name in ordered if name in packages]
        capability_order.extend(name for name in packages if name not in capability_order)

    for capability in capability_order:
        implementation = packages[capability]

        if implementation == "unresolved":
            continue

        pkg_list = ctx.packages.get(implementation, {}).get("packages", [])

        target_projects = package_target_projects(ctx, capability, project_map)
        if not target_projects:
            target_projects = [default_project]

        for package in pkg_list:
            package_name, package_version = resolve_package(package, ctx.versions)
            for target_project in target_projects:
                command = [
                    "add",
                    target_project,
                    "package",
                    package_name,
                    "--no-restore",
                ]
                if package_version:
                    command.extend(["--version", package_version])

                run_dotnet(command, cwd=ctx.output_dir)

def package_target_projects(ctx, capability: str, project_map):
    if capability in {"logging", "validation", "mapping"}:
        project = first_existing_project(ctx, ["API", "Presentation", "Gateway"])
        return [project] if project else []

    if capability == "cqrs":
        projects = [
            project_path(ctx, "Application"),
            first_existing_project(ctx, ["API", "Presentation", "Gateway"]),
        ]
        return unique_existing_projects(projects)

    target_layer = project_map.get(capability, "Application")
    project = project_path(ctx, target_layer)
    return [project] if os.path.exists(project) else []


def unique_existing_projects(projects):
    result = []
    seen = set()
    for project in projects:
        if not project or not os.path.exists(project):
            continue
        normalized = os.path.abspath(project)
        if normalized in seen:
            continue
        seen.add(normalized)
        result.append(project)

    return result


def resolve_package(package, versions):
    if isinstance(package, str):
        return package, None

    if not isinstance(package, dict):
        raise ValueError(f"Unsupported package entry: {package!r}")

    name = package.get("name")
    version_key = package.get("version")

    if not name:
        raise ValueError(f"Package entry is missing a name: {package!r}")

    if not version_key:
        return name, None

    return name, versions.get(version_key, version_key)
