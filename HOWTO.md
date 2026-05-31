# PSE Usage

This guide explains the DSL grammar and how heuristics work.
It also documents templates and the CLI entrypoint.

## DSL grammar overview

The DSL describes intent and structure, not implementations.

Minimal skeleton:

```text
Project StoreApi target=dotnet {
    Archetype WebApi
    Deployment Docker
}
```

### Supported constructs

- `Project <Name> target=<dotnet|java>`: root declaration.
- `Archetype <Name>`: project layout (e.g., WebApi, CleanArchitecture, ModularMonolith, Microservices).
- `Capabilities { Capability <Name> }`: optional explicit capability selections.
- `Context <Name> { ... }`: bounded context.
- `Entity <Name> { <Type> <Name> }`: domain entity with properties.
- `ValueObject <Name> { <Type> <Name> }`: domain value object.
- `Aggregate <Name> { root <Entity> children <Entity> }`: aggregates referencing entities.
- `Infrastructure { Database <Name> Cache <Name> MessageBroker <Name> }`: infra intent.
- `Deployment <Name>`: deployment target (e.g., Docker).

Example with capabilities and infrastructure:

```text
Project StoreApi target=dotnet {
    Archetype WebApi

    Capabilities {
        Capability Logging
        Capability Validation
        Capability Mapping
        Capability Testing
    }

    Context Orders {
        Entity Order {
            Guid Id
            DateTime CreatedAt
            String Status
        }

        Entity OrderItem {
            Guid ProductId
            Int Quantity
        }

        Aggregate OrderAggregate {
            root Order
            children OrderItem
        }
    }

    Infrastructure {
        Database PostgreSQL
        Cache Redis
        MessageBroker RabbitMQ
    }

    Deployment Docker
}
```

## Heuristics: what they are

Heuristics are YAML registries that map architectural intent to concrete choices. They enable the system to stay technology-agnostic and let you swap implementations without changing the DSL.

Core files:

- `pse/heuristics/archetypes.yaml`: maps archetypes to default capability sets.
- `pse/heuristics/presets.yaml`: maps archetypes to capability implementations.
- `pse/heuristics/packages.yaml`: maps implementations to package lists.
- `pse/heuristics/versions.yaml`: central versions registry.
- `pse/heuristics/capabilities.yaml`: dependency metadata between capabilities.

## What users should modify

Recommended user-owned changes:

- `presets.yaml`: pick preferred implementations (e.g., cqrs: mediatr).
- `packages.yaml`: add or change packages for a given implementation.
- `versions.yaml`: bump tool/library versions (dotnet, postgres, redis, etc.).
- `capabilities.yaml`: add new capabilities or dependencies between them.

Usually left alone:

- `archetypes.yaml`: only change if you want different default capability sets per archetype.

## Templates

All generated file bodies come from templates in [pse/templates/dotnet](pse/templates/dotnet).
Edit those files to customize output without changing generator logic.

## How capability selection works

- Presets provide defaults based on archetype.
- Infrastructure implies capabilities (database, cache, messaging).
- DSL `Capabilities { ... }` overrides or augments presets.
- The resolver chooses implementations from presets or defaults in the registry.

The resolved capabilities are recorded in `pse.manifest.json` in the output folder.

## Quick run

```bash
python run.py sample_with_capabilities.pse -o ./sample_output
```

CLI usage:

```bash
python run.py <dsl_file> -o <output_dir>
```
