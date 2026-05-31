import os

from .template_loader import render_template


def create_docker(ctx):

    if ctx.architecture.deployment.target != "Docker":
        return

    write_dockerfile(ctx)
    write_compose(ctx)


def write_dockerfile(ctx):
    name = ctx.architecture.project.name
    version = ctx.versions.get("dotnet", "9.0")

    content = render_template(
        "Dockerfile.tmpl",
        {
            "DotnetVersion": version,
            "ProjectName": name,
        }
    )

    path = os.path.join(ctx.output_dir, "Dockerfile")

    with open(path, "w", encoding="utf-8") as f:
        f.write(content)


def write_compose(ctx):
    name = ctx.architecture.project.name
    infra = ctx.architecture.infrastructure

    services = [
        f"  {name.lower()}:",
        "    build: .",
        f"    container_name: {name.lower()}",
        "    ports:",
        "      - \"8080:8080\"",
    ]

    depends_on = []
    extras = []

    if infra and infra.database and infra.database.type:
        db_type = infra.database.type.lower()
        if db_type == "postgresql" or db_type == "postgres":
            depends_on.append("db")
            extras.extend([
                "  db:",
                f"    image: postgres:{ctx.versions.get('postgres', '17')}",
                "    container_name: postgres",
                "    environment:",
                "      POSTGRES_USER: postgres",
                "      POSTGRES_PASSWORD: postgres",
                "      POSTGRES_DB: app",
                "    ports:",
                "      - \"5432:5432\"",
            ])

    if infra and infra.cache and infra.cache.type:
        cache_type = infra.cache.type.lower()
        if cache_type == "redis":
            depends_on.append("redis")
            extras.extend([
                "  redis:",
                f"    image: redis:{ctx.versions.get('redis', '8')}",
                "    container_name: redis",
                "    ports:",
                "      - \"6379:6379\"",
            ])

    if infra and infra.broker and infra.broker.type:
        broker_type = infra.broker.type.lower()
        if broker_type == "rabbitmq":
            depends_on.append("rabbitmq")
            extras.extend([
                "  rabbitmq:",
                f"    image: rabbitmq:{ctx.versions.get('rabbitmq', '4')}",
                "    container_name: rabbitmq",
                "    ports:",
                "      - \"5672:5672\"",
                "      - \"15672:15672\"",
            ])

    if depends_on:
        services.append("    depends_on:")
        services.extend([f"      - {dep}" for dep in depends_on])

    services_block = "\n".join(services)
    dependencies_block = ""

    if extras:
        dependencies_block = "\n".join(["  # dependencies", *extras])

    content = render_template(
        "docker-compose.yml.tmpl",
        {
            "Services": services_block,
            "Dependencies": dependencies_block,
        }
    )

    path = os.path.join(ctx.output_dir, "docker-compose.yml")

    with open(path, "w", encoding="utf-8") as f:
        f.write(content if content.endswith("\n") else content + "\n")