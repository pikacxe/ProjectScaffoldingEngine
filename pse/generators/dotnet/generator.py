from .solution import create_solution
from .projects import create_projects
from .structure import create_structure
from .integration import create_integration
from .nuget import restore_packages
from .docker import create_docker
from .cleanup import clean_solution


def generate_dotnet(ctx):

    ctx.log("🚀 Generating .NET solution...")

    create_solution(ctx)
    create_projects(ctx)
    create_structure(ctx)
    create_integration(ctx)
    restore_packages(ctx)
    create_docker(ctx)
    clean_solution(ctx)

    ctx.log("✅ .NET generation complete")