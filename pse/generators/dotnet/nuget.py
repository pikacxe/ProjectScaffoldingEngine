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
        "logging": "Application",
        "validation": "Application",
        "mapping": "Application",
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


def restore_packages(ctx):

    packages = resolve_packages(ctx)
    project_map = capability_project_map()
    default_project = project_path(ctx, "Application")

    for capability, implementation in packages.items():

        if implementation == "unresolved":
            continue

        pkg_list = ctx.packages.get(implementation, {}).get("packages", [])

        target_layer = project_map.get(capability, "Application")
        target_project = project_path(ctx, target_layer)

        if not os.path.exists(target_project):
            target_project = default_project

        for pkg in pkg_list:
            run_dotnet([
                "add",
                target_project,
                "package", pkg
            ], cwd=ctx.output_dir)
