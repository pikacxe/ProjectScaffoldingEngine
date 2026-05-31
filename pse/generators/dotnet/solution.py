import subprocess


def create_solution(ctx):
    name = ctx.architecture.project.name

    subprocess.run([
        "dotnet", "new", "sln",
        "-n", name,
        "--format", "sln",
        "--force"
    ], cwd=ctx.output_dir)