from pse.generators.dotnet.process import run_dotnet


def create_solution(ctx):
    name = ctx.architecture.project.name

    run_dotnet([
        "new", "sln",
        "-n", name,
        "--format", "slnx",
        "--force"
    ], cwd=ctx.output_dir)
