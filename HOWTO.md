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

Key integration templates:

- `Program.cs.tmpl`: entrypoint wiring for infra.
- `AppSettings.json.tmpl` and `AppSettings.Development.json.tmpl`.
- `DbContext.cs.tmpl` for database context.
- `OptionsClass.cs.tmpl` for options types.
- `Controller.cs.tmpl` and `ControllerMethods.cs.tmpl` for thin CRUD controllers that call repositories.
- `RepositoryInterface.cs.tmpl` and `RepositoryImplementation.cs.tmpl` for generic CRUD repository scaffolding.
- `TestClass.cs.tmpl` for xUnit placeholder tests.

## How capability selection works

- Presets provide defaults based on archetype.
- Infrastructure implies capabilities (database, cache, messaging).
- DSL `Capabilities { ... }` overrides or augments presets.
- The resolver chooses implementations from presets or defaults in the registry.

The resolved capabilities are recorded in `pse.manifest.json` in the output folder, along with run status, error text when generation fails, and a finish timestamp.

## Generated project shape

The current dotnet output is intentionally thin and generic:

- API controllers inject repositories and expose a CRUD surface.
- Domain repositories define CRUD methods per entity.
- Infrastructure repositories provide stub implementations that are meant to be extended.
- Test projects get a simple xUnit fact per entity so the project starts with a working shape.

## Quick run

```bash
pse sample_with_capabilities.pse -o ./sample_output
```

CLI usage:

```bash
pse <dsl_file> -o <output_dir>
```

The same generator is registered with textX and can be discovered by the `textx` command:

```bash
textx list-generators
textx generate pse/sample_with_capabilities.pse --target dotnet -o ./sample_output --overwrite
```

## textX-LS editor support

PSE is registered as a textX language package, so editor support is provided through the upstream `textX-LS` project rather than a custom language server. `textX-LS` discovers PSE through the `textx_languages` entry point after this project is installed.

PSE contributes the following textX integration points:

- language: `pse (*.pse)`
- generator: `pse -> dotnet`
- syntax parsing: `pse/grammar/pse.tx`, loaded through `textx.metamodel_from_file`
- semantic checks: `pse.validation.validate_model`

Install PSE in the same Python environment used by `textX-LS`:

```bash
pip install -e ".[editor]"
textx list-languages
textx check pse/sample.pse
```

Expected discovery output includes:

```text
pse (*.pse)    pse    Project Scaffolding Engine DSL.
```

To use `textX-LS`, install and run the upstream textX-LS VS Code extension/client as documented in the textX-LS repository. Once the extension uses an environment where PSE is installed, `.pse` files are handled as a registered textX language.

Useful validation commands before opening the editor:

```bash
textx check pse/sample.pse
textx check pse/sample_with_capabilities.pse
```

Generate and install the VS Code extension for `.pse` files:

```bash
pse-vscode-extension --output dist/pse-0.1.0.vsix
code --install-extension dist/pse-0.1.0.vsix
```

The generated extension contributes `.pse` file recognition and TextMate syntax highlighting. It depends on the upstream `textX.textX` VS Code extension, which runs textX-LS and provides validation, completion, definitions, references, folding, symbols, and generator integration. PSE does not implement a separate LSP transport.
