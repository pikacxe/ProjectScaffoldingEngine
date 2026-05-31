from .solution import create_solution
from .projects import create_projects
from .nuget import restore_packages
from .docker import create_docker


def generate_dotnet(ctx):

    ctx.log("🚀 Generating .NET solution...")

    create_solution(ctx)
    create_projects(ctx)
    restore_packages(ctx)
    create_docker(ctx)

    ctx.log("✅ .NET generation complete")