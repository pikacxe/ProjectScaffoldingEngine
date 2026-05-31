import os
import subprocess

from .template_loader import render_template


def archetype_layers(archetype: str):
    return {
        "WebApi": ["API", "Application", "Domain", "Infrastructure", "Tests"],
        "CleanArchitecture": ["Presentation", "Application", "Domain", "Infrastructure"],
        "ModularMonolith": ["Modules"],
        "Microservices": ["Services", "Gateway", "Shared", "Infrastructure"]
    }.get(archetype, ["Core"])


def create_projects(ctx):

    base = ctx.architecture.project.name
    layers = archetype_layers(ctx.architecture.project.archetype)
    output_dir = os.path.abspath(ctx.output_dir)
    solution_path = os.path.join(output_dir, f"{base}.slnx")

    for layer in layers:
        project_name = f"{base}.{layer}"
        project_dir = os.path.join(output_dir, project_name)
        project_file = os.path.join(project_dir, f"{project_name}.csproj")
        template = project_template(layer)

        subprocess.run([
            "dotnet", "new", template,
            "-o", project_dir,
            "--force"
        ])

        cleanup_default_files(project_dir)
        ensure_program(project_dir, project_name, layer)

        subprocess.run([
            "dotnet", "sln", solution_path, "add", project_file
        ], cwd=output_dir)

    add_project_references(ctx, output_dir, base, layers)


def project_template(layer: str):
    if layer in {"API", "Presentation", "Gateway"}:
        return "webapi"

    return "classlib"


def cleanup_default_files(project_dir: str):
    class_file = os.path.join(project_dir, "Class1.cs")
    if os.path.exists(class_file):
        os.remove(class_file)


def ensure_program(project_dir: str, project_name: str, layer: str):
    if layer not in {"API", "Presentation", "Gateway"}:
        return

    program_path = os.path.join(project_dir, "Program.cs")
    content = render_template("Program.cs.tmpl", {})

    with open(program_path, "w", encoding="utf-8") as f:
        f.write(content)


def add_project_references(ctx, output_dir: str, base: str, layers):
    layer_paths = {
        layer: os.path.join(output_dir, f"{base}.{layer}", f"{base}.{layer}.csproj")
        for layer in layers
    }

    def add_ref(source_layer: str, target_layer: str):
        source = layer_paths.get(source_layer)
        target = layer_paths.get(target_layer)

        if not source or not target:
            return

        if not os.path.exists(source) or not os.path.exists(target):
            return

        subprocess.run(["dotnet", "add", source, "reference", target], cwd=output_dir)

    if "API" in layers:
        add_ref("API", "Application")

    if "Application" in layers:
        add_ref("Application", "Domain")

    if "Infrastructure" in layers:
        add_ref("Infrastructure", "Application")
        add_ref("Infrastructure", "Domain")

    if "Tests" in layers:
        add_ref("Tests", "Application")
        add_ref("Tests", "Domain")