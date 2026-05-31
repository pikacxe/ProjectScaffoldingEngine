import os


def create_docker(ctx):

    if ctx.architecture.deployment.target != "Docker":
        return

    name = ctx.architecture.project.name

    content = f"""
FROM mcr.microsoft.com/dotnet/aspnet:{ctx.versions.get("dotnet", "9.0")}
WORKDIR /app
COPY . .
ENTRYPOINT ["dotnet", "{name}.API.dll"]
"""

    path = os.path.join(ctx.output_dir, "Dockerfile")

    with open(path, "w") as f:
        f.write(content)