from .capabilities import capability_enabled, capability_value


def build_program_values(ctx, layer: str):
    infra = ctx.architecture.infrastructure
    base = ctx.architecture.project.name
    contexts = ctx.architecture.contexts

    using_lines = []
    host_configuration = []
    service_registrations = []
    registrations = []
    health_checks = [
        "builder.Services.AddHealthChecks()",
        "    .AddCheck(\"self\", () => HealthCheckResult.Healthy(), tags: new[] { \"live\" })",
    ]
    using_lines.extend([
        "using Microsoft.AspNetCore.Diagnostics.HealthChecks;\n",
        "using Microsoft.Extensions.Diagnostics.HealthChecks;\n",
    ])

    entities = [
        entity
        for context in contexts or []
        for entity in getattr(context, "entities", []) or []
    ]

    add_capability_registrations(
        ctx,
        layer,
        base,
        entities,
        using_lines,
        host_configuration,
        service_registrations,
    )
    add_application_registrations(base, entities, using_lines, service_registrations)
    add_infrastructure_registrations(
        infra,
        base,
        entities,
        using_lines,
        service_registrations,
        registrations,
        health_checks,
    )

    return {
        "UsingLines": render_block(using_lines, joiner=""),
        "HostConfiguration": render_block(host_configuration),
        "ServiceRegistrations": render_block(service_registrations),
        "InfraRegistrations": render_block(registrations),
        "InfraPipeline": build_infrastructure_pipeline(infra),
        "HealthChecks": render_health_checks(health_checks),
    }


def add_capability_registrations(
    ctx,
    layer,
    base,
    entities,
    using_lines,
    host_configuration,
    service_registrations,
):
    if capability_enabled(ctx, "logging"):
        using_lines.append("using Serilog;\n")
        host_configuration.extend([
            "builder.Host.UseSerilog((context, services, loggerConfiguration) =>",
            "    loggerConfiguration",
            "        .ReadFrom.Configuration(context.Configuration)",
            "        .ReadFrom.Services(services)",
            "        .WriteTo.Console());",
            "",
        ])

    if capability_enabled(ctx, "validation"):
        using_lines.extend(["using FluentValidation;\n", "using FluentValidation.AspNetCore;\n"])
        service_registrations.extend([
            "builder.Services.AddFluentValidationAutoValidation();",
            "builder.Services.AddValidatorsFromAssemblyContaining<Program>();",
            "",
        ])

    if capability_enabled(ctx, "mapping"):
        using_lines.extend([
            "using Mapster;\n",
            "using MapsterMapper;\n",
            f"using {base}.{layer}.Mapping;\n",
        ])
        service_registrations.extend([
            "MappingConfig.Register();",
            "builder.Services.AddMapster();",
            "",
        ])

    add_cqrs_registrations(
        capability_value(ctx, "cqrs"),
        base,
        entities,
        using_lines,
        host_configuration,
        service_registrations,
    )


def add_cqrs_registrations(
    implementation,
    base,
    entities,
    using_lines,
    host_configuration,
    service_registrations,
):
    first_entity = entities[0] if entities else None
    if implementation == "mediatr" and first_entity:
        using_lines.append(f"using {base}.Application.Cqrs;\n")
        service_registrations.extend([
            f"builder.Services.AddMediatR(cfg => cfg.RegisterServicesFromAssemblyContaining<GetAll{first_entity.name}QueryHandler>());",
            "",
        ])
    elif implementation == "wolverine":
        using_lines.append("using Wolverine;\n")
        if first_entity:
            using_lines.append(f"using {base}.Application.Cqrs;\n")
            host_configuration.extend([
                "builder.Host.UseWolverine(options =>",
                "{",
                f"    options.Discovery.IncludeAssembly(typeof(GetAll{first_entity.name}Query).Assembly);",
                "});",
                "",
            ])
        else:
            host_configuration.extend(["builder.Host.UseWolverine();", ""])


def add_application_registrations(base, entities, using_lines, registrations):
    if not entities:
        return

    using_lines.extend([
        f"using {base}.Application.Interfaces;\n",
        f"using {base}.Application.Services;\n",
    ])
    registrations.extend(
        f"builder.Services.AddScoped<I{entity.name}Service, {entity.name}Service>();"
        for entity in entities
    )
    registrations.append("")


def add_infrastructure_registrations(infra, base, entities, using_lines, services, registrations, health_checks):
    if entities:
        using_lines.extend([
            f"using {base}.Domain.Repositories;\n",
            f"using {base}.Infrastructure.Repositories;\n",
        ])
        repository_lifetime = "Scoped" if infra and infra.database else "Singleton"
        for entity in entities:
            services.append(
                f"builder.Services.Add{repository_lifetime}<I{entity.name}Repository, {entity.name}Repository>();"
            )
        services.append("")

    if infra and infra.database:
        using_lines.extend([
            "using Microsoft.EntityFrameworkCore;\n",
            f"using {base}.Infrastructure.Persistence;\n",
        ])
        registrations.extend([
            "builder.Services.AddDbContext<AppDbContext>(options =>",
            "    options.UseNpgsql(builder.Configuration.GetConnectionString(\"Database\")));",
            "",
        ])
        health_checks.append(
            "    .AddDbContextCheck<AppDbContext>(\"database\", tags: new[] { \"ready\" })"
        )

    if infra and infra.cache:
        registrations.extend([
            "builder.Services.AddStackExchangeRedisCache(options =>",
            "    options.Configuration = builder.Configuration.GetConnectionString(\"Redis\"));",
            "",
        ])

    if infra and infra.broker:
        using_lines.append("using MassTransit;\n")
        registrations.extend([
            "builder.Services.AddMassTransit(x =>",
            "{",
            "    x.UsingRabbitMq((context, cfg) =>",
            "    {",
            "        cfg.Host(builder.Configuration.GetConnectionString(\"RabbitMq\"));",
            "    });",
            "});",
            "",
        ])


def render_block(lines, joiner="\n"):
    block = joiner.join(lines)
    return f"{block}\n" if block else ""


def render_health_checks(lines):
    return "\n".join(lines) + ";\n"


def build_infrastructure_pipeline(infra):
    if not infra or not infra.database:
        return ""

    return "\n".join([
        "using (var scope = app.Services.CreateScope())",
        "{",
        "    var dbContext = scope.ServiceProvider.GetRequiredService<AppDbContext>();",
        "    dbContext.Database.EnsureCreated();",
        "}",
        "",
    ])
