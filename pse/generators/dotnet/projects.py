import os
import subprocess


def archetype_layers(archetype: str):
    return {
        "WebApi": ["API", "Application", "Domain", "Infrastructure", "Tests"],
        "CleanArchitecture": ["Presentation", "Application", "Domain", "Infrastructure"],
        "ModularMonolith": ["Modules"]
    }.get(archetype, ["Core"])


def create_projects(ctx):

    base = ctx.architecture.project.name
    layers = archetype_layers(ctx.architecture.project.archetype)
    output_dir = os.path.abspath(ctx.output_dir)
    solution_path = os.path.join(output_dir, f"{base}.sln")

    for layer in layers:
        project_name = f"{base}.{layer}"
        project_dir = os.path.join(output_dir, project_name)
        project_file = os.path.join(project_dir, f"{project_name}.csproj")

        subprocess.run([
            "dotnet", "new", "classlib",
            "-o", project_dir,
            "--force"
        ])

        subprocess.run([
            "dotnet", "sln", solution_path, "add", project_file
        ], cwd=output_dir)