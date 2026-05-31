import os
import subprocess


def clean_solution(ctx):
    output_dir = os.path.abspath(ctx.output_dir)

    if not os.path.isdir(output_dir):
        return

    subprocess.run(["dotnet", "clean"], cwd=output_dir)
