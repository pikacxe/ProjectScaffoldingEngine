import os

from .structure_helpers import pick_id_property_name
from .template_loader import render_template


def create_integration(ctx):
    write_appsettings(ctx)
    write_db_context(ctx)


def write_appsettings(ctx):
    output_dir = os.path.abspath(ctx.output_dir)
    base = ctx.architecture.project.name
    infra = ctx.architecture.infrastructure

    entrypoints = [
        os.path.join(output_dir, f"{base}.API"),
        os.path.join(output_dir, f"{base}.Presentation"),
        os.path.join(output_dir, f"{base}.Gateway"),
    ]

    connection_lines = []
    if infra and infra.database:
        connection_lines.append("    \"Database\": \"Host=localhost;Port=5432;Database=app;Username=postgres;Password=postgres\"")

    if infra and infra.cache:
        connection_lines.append("    \"Redis\": \"localhost:6379\"")

    if infra and infra.broker:
        connection_lines.append("    \"RabbitMq\": \"amqp://app:rabbitmq@localhost:5672\"")

    connection_block = ",\n".join(connection_lines)
    connection_strings_block = ""
    if connection_block:
        connection_strings_block = (
            "  \"ConnectionStrings\": {\n"
            + connection_block
            + "\n  },\n"
        )

    content = render_template(
        "AppSettings.json.tmpl",
        {
            "ConnectionStringsBlock": connection_strings_block,
        }
    )

    dev_content = render_template(
        "AppSettings.Development.json.tmpl",
        {
            "ConnectionStringsBlock": connection_strings_block,
        }
    )

    for path in entrypoints:
        if not os.path.isdir(path):
            continue

        write_file(os.path.join(path, "appsettings.json"), content)
        write_file(os.path.join(path, "appsettings.Development.json"), dev_content)


def write_db_context(ctx):
    output_dir = os.path.abspath(ctx.output_dir)
    base = ctx.architecture.project.name
    infra = ctx.architecture.infrastructure

    if not infra or not infra.database:
        return

    infra_root = os.path.join(output_dir, f"{base}.Infrastructure")
    if not os.path.isdir(infra_root):
        return

    persistence_root = os.path.join(infra_root, "Persistence")
    os.makedirs(persistence_root, exist_ok=True)

    namespace = f"{base}.Infrastructure.Persistence"
    entities = [
        entity
        for context in ctx.architecture.contexts or []
        for entity in context.entities
    ]
    db_sets = "".join(
        f"    public DbSet<{entity.name}> {entity.name}Set => Set<{entity.name}>();\n"
        for entity in entities
    )
    key_configurations = "".join(
        f"        modelBuilder.Entity<{entity.name}>().HasKey(entity => entity.{pick_id_property_name(entity.properties)});\n"
        for entity in entities
    )
    content = render_template(
        "DbContext.cs.tmpl",
        {
            "Namespace": namespace,
            "ClassName": "AppDbContext",
            "DomainNamespace": f"{base}.Domain",
            "DbSets": db_sets,
            "KeyConfigurations": key_configurations,
        }
    )

    write_file(os.path.join(persistence_root, "AppDbContext.cs"), content)


def write_file(path: str, content: str):
    with open(path, "w", encoding="utf-8") as f:
        f.write(content if content.endswith("\n") else content + "\n")
