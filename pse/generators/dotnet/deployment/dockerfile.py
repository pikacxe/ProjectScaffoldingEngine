import os

from ..template_loader import render_template
from .common import write_text


def write_dockerfile(ctx, spec):
    content = render_template(
        "Dockerfile.tmpl",
        {
            "DotnetVersion": spec.dotnet_version,
            "EntrypointProject": spec.entrypoint_project,
        },
    )
    write_text(os.path.join(ctx.output_dir, "Dockerfile"), content)
