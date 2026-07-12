import copy
import tempfile

from pse.generation_ownership import publish_generated_tree

from .solution import create_solution
from .projects import create_projects
from .structure import create_structure
from .integration import create_integration
from .nuget import configure_packages
from .deployment import create_deployment
from .cleanup import clean_solution


def generate_dotnet(ctx):
    overwrite = ctx.options.get("overwrite", True)
    with tempfile.TemporaryDirectory(prefix="pse-dotnet-") as staging_dir:
        staging_ctx = copy.copy(ctx)
        staging_ctx.output_dir = staging_dir
        generate_dotnet_staging(staging_ctx)
        publish_generated_tree(staging_dir, ctx.output_dir, overwrite)


def generate_dotnet_staging(ctx):

    ctx.log("🚀 Generating .NET solution...")

    create_solution(ctx)
    create_projects(ctx)
    create_structure(ctx)
    create_integration(ctx)
    configure_packages(ctx)
    create_deployment(ctx)
    clean_solution(ctx)

    ctx.log("✅ .NET generation complete")
