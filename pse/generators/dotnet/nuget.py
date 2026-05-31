import subprocess


def resolve_packages(ctx):
    archetype = ctx.architecture.project.archetype.lower()
    preset = ctx.presets.get(archetype, {})

    return preset.get("capabilities", {})


def restore_packages(ctx):

    packages = resolve_packages(ctx)

    target_project = f"{ctx.architecture.project.name}.Application"

    for capability, implementation in packages.items():

        pkg_list = ctx.packages.get(implementation, {}).get("packages", [])

        for pkg in pkg_list:
            subprocess.run([
                "dotnet", "add",
                target_project,
                "package", pkg
            ], cwd=ctx.output_dir)