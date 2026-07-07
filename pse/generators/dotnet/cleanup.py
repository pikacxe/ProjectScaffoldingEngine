import os

from pse.generators.dotnet.process import run_dotnet


def clean_solution(ctx):
    output_dir = os.path.abspath(ctx.output_dir)

    if not os.path.isdir(output_dir):
        return

    run_dotnet(["clean"], cwd=output_dir)
