import os

from .template_loader import render_template


def create_integration(ctx):
    write_appsettings(ctx)
    write_options(ctx)
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
    section_lines = []

    if infra and infra.database:
        connection_lines.append("    \"Database\": \"Host=localhost;Port=5432;Database=app;Username=postgres;Password=postgres\"")
        section_lines.extend([
            "  \"Database\": {",
            "    \"Provider\": \"Postgres\"",
            "  },",
        ])

    if infra and infra.cache:
        connection_lines.append("    \"Redis\": \"localhost:6379\"")
        section_lines.extend([
            "  \"Redis\": {",
            "    \"Enabled\": true",
            "  },",
        ])

    if infra and infra.broker:
        connection_lines.append("    \"RabbitMq\": \"amqp://guest:guest@localhost:5672\"")
        section_lines.extend([
            "  \"RabbitMq\": {",
            "    \"Enabled\": true",
            "  },",
        ])

    connection_block = ",\n".join(connection_lines)
    section_block = "\n".join(section_lines)

    connection_strings_block = ""
    if connection_block:
        connection_strings_block = (
            "  \"ConnectionStrings\": {\n"
            + connection_block
            + "\n  },\n"
        )

    if section_block:
        section_block = section_block.rstrip(",") + ",\n"

    content = render_template(
        "AppSettings.json.tmpl",
        {
            "ConnectionStringsBlock": connection_strings_block,
            "InfraSections": section_block,
        }
    )

    dev_content = render_template(
        "AppSettings.Development.json.tmpl",
        {
            "ConnectionStringsBlock": connection_strings_block,
            "InfraSections": section_block,
        }
    )

    for path in entrypoints:
        if not os.path.isdir(path):
            continue

        write_file(os.path.join(path, "appsettings.json"), content)
        write_file(os.path.join(path, "appsettings.Development.json"), dev_content)


def write_options(ctx):
    output_dir = os.path.abspath(ctx.output_dir)
    base = ctx.architecture.project.name
    infra = ctx.architecture.infrastructure

    app_root = os.path.join(output_dir, f"{base}.Application")
    if not os.path.isdir(app_root):
        return

    options_root = os.path.join(app_root, "Options")
    os.makedirs(options_root, exist_ok=True)

    namespace = f"{base}.Application.Options"

    if infra and infra.database:
        body = "    public string ConnectionString { get; set; } = string.Empty;\n"
        write_options_class(options_root, namespace, "DatabaseOptions", body)

    if infra and infra.cache:
        body = "    public string ConnectionString { get; set; } = string.Empty;\n"
        write_options_class(options_root, namespace, "RedisOptions", body)

    if infra and infra.broker:
        body = (
            "    public string Host { get; set; } = string.Empty;\n"
            "    public string Username { get; set; } = \"guest\";\n"
            "    public string Password { get; set; } = \"guest\";\n"
        )
        write_options_class(options_root, namespace, "RabbitMqOptions", body)


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
    content = render_template(
        "DbContext.cs.tmpl",
        {
            "Namespace": namespace,
            "ClassName": "AppDbContext",
        }
    )

    write_file(os.path.join(persistence_root, "AppDbContext.cs"), content)


def write_options_class(options_root: str, namespace: str, class_name: str, body: str):
    content = render_template(
        "OptionsClass.cs.tmpl",
        {
            "Namespace": namespace,
            "ClassName": class_name,
            "Body": body,
        }
    )

    write_file(os.path.join(options_root, f"{class_name}.cs"), content)


def write_file(path: str, content: str):
    with open(path, "w", encoding="utf-8") as f:
        f.write(content if content.endswith("\n") else content + "\n")
