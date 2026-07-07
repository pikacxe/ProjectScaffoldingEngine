import os

from pse.generators.dotnet.process import run_dotnet
from .template_loader import render_template


def archetype_layers(archetype: str):
    return {
        "WebApi": ["API", "Application", "Domain", "Infrastructure", "Tests"],
        "CleanArchitecture": ["Presentation", "Application", "Domain", "Infrastructure"],
        "ModularMonolith": ["Modules"],
        "Microservices": ["Services", "Gateway", "Shared", "Infrastructure"]
    }.get(archetype, ["Core"])


def create_projects(ctx):

    base = ctx.architecture.project.name
    layers = archetype_layers(ctx.architecture.project.archetype)
    output_dir = os.path.abspath(ctx.output_dir)
    solution_path = os.path.join(output_dir, f"{base}.slnx")

    for layer in layers:
        project_name = f"{base}.{layer}"
        project_dir = os.path.join(output_dir, project_name)
        project_file = os.path.join(project_dir, f"{project_name}.csproj")
        template = project_template(layer)

        run_dotnet([
            "new", template,
            "-o", project_dir,
            "--force"
        ])

        cleanup_default_files(project_dir)
        cleanup_webapi_package_refs(project_dir, template)
        ensure_program(project_dir, project_name, layer, ctx)

        run_dotnet([
            "sln", solution_path, "add", project_file
        ], cwd=output_dir)

    add_project_references(ctx, output_dir, base, layers)


def project_template(layer: str):
    if layer in {"API", "Presentation", "Gateway"}:
        return "webapi"

    return "classlib"


def cleanup_webapi_package_refs(project_dir: str, template: str):
    if template != "webapi":
        return

    project_file = next(
        (os.path.join(project_dir, name) for name in os.listdir(project_dir) if name.endswith(".csproj")),
        None,
    )

    if not project_file:
        return

    with open(project_file, "r", encoding="utf-8") as f:
        lines = f.readlines()

    filtered = [line for line in lines if "Microsoft.AspNetCore.OpenApi" not in line]

    if filtered == lines:
        return

    with open(project_file, "w", encoding="utf-8") as f:
        f.writelines(filtered)


def cleanup_default_files(project_dir: str):
    class_file = os.path.join(project_dir, "Class1.cs")
    if os.path.exists(class_file):
        os.remove(class_file)


def ensure_program(project_dir: str, project_name: str, layer: str, ctx):
    if layer not in {"API", "Presentation", "Gateway"}:
        return

    program_path = os.path.join(project_dir, "Program.cs")
    content = render_template("Program.cs.tmpl", build_program_values(ctx))

    with open(program_path, "w", encoding="utf-8") as f:
        f.write(content)


def build_program_values(ctx):
    infra = ctx.architecture.infrastructure
    base = ctx.architecture.project.name

    using_lines = []
    registrations = []
    pipeline = []

    if infra and (infra.database or infra.cache or infra.broker):
        using_lines.append(f"using {base}.Application.Options;\n")

    if infra and infra.database:
        using_lines.append("using Microsoft.EntityFrameworkCore;\n")
        using_lines.append(f"using {base}.Infrastructure.Persistence;\n")
        registrations.extend([
            "builder.Services.Configure<DatabaseOptions>(builder.Configuration.GetSection(\"Database\"));",
            "builder.Services.AddDbContext<AppDbContext>(options =>",
            "    options.UseNpgsql(builder.Configuration.GetConnectionString(\"Database\")));",
            "",
        ])

    if infra and infra.cache:
        registrations.extend([
            "builder.Services.Configure<RedisOptions>(builder.Configuration.GetSection(\"Redis\"));",
            "builder.Services.AddStackExchangeRedisCache(options =>",
            "    options.Configuration = builder.Configuration.GetConnectionString(\"Redis\"));",
            "",
        ])

    if infra and infra.broker:
        using_lines.append("using MassTransit;\n")
        registrations.extend([
            "builder.Services.Configure<RabbitMqOptions>(builder.Configuration.GetSection(\"RabbitMq\"));",
            "builder.Services.AddMassTransit(x =>",
            "{",
            "    x.UsingRabbitMq((context, cfg) =>",
            "    {",
            "        cfg.Host(builder.Configuration.GetConnectionString(\"RabbitMq\"));",
            "    });",
            "});",
            "",
        ])

    using_block = "".join(using_lines)
    registrations_block = "\n".join(registrations)
    pipeline_block = "\n".join(pipeline)

    if using_block:
        using_block += "\n"

    if registrations_block:
        registrations_block += "\n"

    if pipeline_block:
        pipeline_block += "\n"

    return {
        "UsingLines": using_block,
        "InfraRegistrations": registrations_block,
        "InfraPipeline": pipeline_block,
    }


def add_project_references(ctx, output_dir: str, base: str, layers):
    layer_paths = {
        layer: os.path.join(output_dir, f"{base}.{layer}", f"{base}.{layer}.csproj")
        for layer in layers
    }

    def add_ref(source_layer: str, target_layer: str):
        source = layer_paths.get(source_layer)
        target = layer_paths.get(target_layer)

        if not source or not target:
            return

        if not os.path.exists(source) or not os.path.exists(target):
            return

        run_dotnet(["add", source, "reference", target], cwd=output_dir)

    if "API" in layers:
        add_ref("API", "Application")
        if ctx.architecture.infrastructure and (ctx.architecture.infrastructure.database or ctx.architecture.infrastructure.cache or ctx.architecture.infrastructure.broker):
            add_ref("API", "Infrastructure")

    if "Application" in layers:
        add_ref("Application", "Domain")

    if "Presentation" in layers:
        if ctx.architecture.infrastructure and (ctx.architecture.infrastructure.database or ctx.architecture.infrastructure.cache or ctx.architecture.infrastructure.broker):
            add_ref("Presentation", "Infrastructure")

    if "Gateway" in layers:
        if ctx.architecture.infrastructure and (ctx.architecture.infrastructure.database or ctx.architecture.infrastructure.cache or ctx.architecture.infrastructure.broker):
            add_ref("Gateway", "Infrastructure")

    if "Infrastructure" in layers:
        add_ref("Infrastructure", "Application")
        add_ref("Infrastructure", "Domain")

    if "Tests" in layers:
        add_ref("Tests", "Application")
        add_ref("Tests", "Domain")
