# Project Scaffolding Engine (PSE)

PSE is a Domain-Driven Design (DDD) architecture scaffolding engine built on top of textX.

Instead of generating folders and files directly, PSE allows developers to describe software architecture using a domain-specific language (DSL). The engine applies architectural heuristics, technology presets, and generation plugins to produce production-ready project structures.

The goal is to provide a consistent, maintainable starting point for modern software projects while remaining technology-agnostic and future-proof.


## Installation

Install from the repository root:

```bash
python -m venv venv
source venv/bin/activate
pip install -e .
```

After installation, PSE is available both as a CLI command and as a registered textX language/generator:

```bash
pse --help
textx list-languages
textx list-generators
```

Expected textX discovery includes:

```text
pse (*.pse)       pse        Project Scaffolding Engine DSL.
pse -> dotnet     pse        Generate a .NET solution from a PSE model.
```

## Quick Usage

Validate a PSE model:

```bash
textx check pse/sample.pse
```

Generate a .NET project through the PSE CLI:

```bash
pse pse/sample_with_capabilities.pse -o ./pse/sample_output
```

Generate through the registered textX generator:

```bash
textx generate pse/sample_with_capabilities.pse --target dotnet -o ./pse/sample_output --overwrite
```

Generated-file hashes are stored in `.pse-generated.json`. The CLI overwrites owned files by default; pass `--no-overwrite` to preserve files you have modified while still refreshing unchanged generated output.

For generated .NET output, the `dotnet` CLI must be installed and available on `PATH`.

For VS Code/textX-LS editor support, install the editor extras:

```bash
pip install -e ".[editor]"
```

---

## Vision

PSE aims to become:

> Terraform for software architecture.

Developers describe:

* Business domains
* Bounded contexts
* Entities
* APIs
* Infrastructure
* Deployment requirements

PSE generates:

* Solution structure
* Source projects
* Thin controllers wired to repositories with generic CRUD starters
* Domain repository interfaces and infrastructure implementations
* Docker configurations
* CI/CD pipelines
* Infrastructure manifests
* Tests

---

## Architecture

PSE follows a layered architecture.

```text
DSL Source
    ↓
AST (textX)
    ↓
Architecture Model (semantic IR)
    ↓
Capability Graph (intent)
    ↓
Dependency Graph (ordering)
    ↓
Generators (backend emission)
```

**DSL (Grammar Layer)**

- Clean, constrained DSL in `pse.tx`.
- Constructs: Project, Archetype, Capabilities, Contexts, Entities, ValueObjects, Aggregates, Infrastructure, Deployment.
- No packages/frameworks/CI/CD in DSL; intent only.

**Architecture Model (Core IR)**

- Normalized `ArchitectureModel` with project metadata, contexts, entities, value objects, aggregates, infrastructure, and deployment.
- Decouples DSL from generators and enables multi-language targets.

**Heuristics System (Externalized Intelligence)**

- YAML registries: `archetypes.yaml`, `presets.yaml`, `packages.yaml`, `versions.yaml`, `capabilities.yaml`.
- Maps archetypes to capabilities, capabilities to implementations, implementations to packages and versions.

**Bootstrap System (Execution Orchestrator)**

- Validates environment, loads grammar, parses DSL, builds `ArchitectureModel`, loads heuristics.
- Performs semantic validation on the parsed DSL before generation.
- Builds `GenerationContext` and dispatches generators.
- Fail-fast, deterministic execution flow.
- Writes a run manifest (`pse.manifest.json`) with DSL input, resolved capabilities, timestamps, status, error text, and finish time.

**GenerationContext (Unified Generator Contract)**

- Shared contract for all generators: architecture model, heuristics, output path, options, logging.
- Removes direct dependency on textX models in generators.

**Dotnet Generator (Pipeline-Based)**

```text
generate_dotnet(ctx)
    ├── create_solution()
    ├── create_projects()
    ├── create_structure()
    ├── create_integration()
    ├── configure_packages()
    ├── create_deployment()
    └── clean_solution()
```

**Deployment Generation**

- `Docker`: multi-stage, non-root image plus a local Compose stack with health checks and persistent dependency volumes.
- `DockerSwarm`: image-based stack, overlay networking, rolling update/rollback policy, resource limits, persistence, and external secrets.
- `Kubernetes`: namespace, stateless API Deployment and Service, probes, resources, restricted security context, and stateful infrastructure workloads with persistent volume claims.
- All targets are selected from the same architecture model. YAML is emitted from structured data; the .NET image uses [pse/templates/dotnet/Dockerfile.tmpl](pse/templates/dotnet/Dockerfile.tmpl).

**Integration Scaffolding**

- Generates `appsettings.json` and `appsettings.Development.json` for entrypoint projects.
- Emits Options classes in `Application/Options` for Database, Redis, and RabbitMq.
- Adds `AppDbContext` in Infrastructure when a database is declared.
- Wires EF Core, Redis cache, and MassTransit in Program.cs using templates.

**Controller and Application Scaffolding**

- Generates thin API controllers that use Application services, or CQRS requests when MediatR/Wolverine is selected.
- Emits CRUD controller actions: `GetAll`, `GetById`, `Create`, `Update`, and `Delete`.
- Application services own the use-case boundary and depend on domain repository interfaces.
- Infrastructure repository implementations remain behind the Application layer.

**Test Scaffolding**

- Generates focused xUnit construction and property assertions per entity.
- Uses one passing fact per test class so the test project starts in a runnable state.

**Capability System + Resolver**

- Capabilities represent abstract needs (cqrs, logging, validation, database, cache, messaging).
- Resolver applies archetype defaults, infers from infrastructure, and falls back to defaults.
- Produces a `CapabilityGraph` used by generators.

**Dependency Graph System (Ordering Engine)**

- Directed dependency graph with topological sorting.
- Enables deterministic capability sequencing and future orchestration correctness.

**Integration Path**

```text
ArchitectureModel
    ↓
CapabilityGraph
    ↓
DependencyGraph
    ↓
GenerationContext
```

Generators are now dumb executors; intelligence is centralized in the resolver layer.

### What This Is Now

PSE is an architecture compilation engine and a declarative, heuristic-driven scaffolding system.

### Future-Proofing Already in Place

- Capability swapping (MediatR → Wolverine, Serilog → built-in logging).
- Multi-language targets via the same semantic model.
- Deployment target evolution through isolated Compose, Swarm, and Kubernetes generators.
- Archetype evolution through the validated Web API and Clean Architecture layouts.


### DSL

The DSL describes architecture and business requirements.

Example:

```text
Project StoreApi target=dotnet {

    Archetype WebApi

    Capabilities {
        Capability Logging
        Capability Validation
        Capability Mapping
    }

    Context Orders {

        Entity Order {
            Guid Id
            DateTime CreatedAt
        }

        Entity OrderItem {
            Guid ProductId
            int Quantity
        }

        Aggregate OrderAggregate {
            root Order
            children OrderItem
        }
    }

    Infrastructure {
        Database PostgreSQL
        Cache Redis
    }

    Deployment Docker
}
```

Samples:

- Basic DSL (no explicit capabilities): [pse/sample_basic.pse](pse/sample_basic.pse)
- DSL with explicit capabilities: [pse/sample_with_capabilities.pse](pse/sample_with_capabilities.pse)

### Templates

Generated text is kept under [pse/templates](pse/templates): .NET source templates live in `dotnet/`, the VS Code extension script in `editor/`, and deployment instructions in `deployment/`. Deployment YAML remains structured Python data so it can be composed and serialized safely.

### Editor Support With textX-LS

PSE is a registered textX language package for `.pse` files. Editor support is provided through the upstream [textX-LS](https://github.com/textX/textX-LS) project, not through a custom language-server implementation.

After installing PSE, textX can discover the language and generator:

```bash
textx list-languages
textx list-generators
textx check pse/sample.pse
```

The registered PSE language uses `pse/grammar/pse.tx` through textX and runs PSE semantic validation as a textX model processor. Install PSE into the same Python environment used by textX-LS so the server can discover `pse (*.pse)`.

To generate a VS Code extension for `.pse` files:

```bash
pip install -e ".[editor]"
pse-vscode-extension --output dist/pse-0.1.0.vsix
code --install-extension dist/pse-0.1.0.vsix
```

### Generated Output Notes

- `pse.manifest.json` is append-only and records `status`, `error`, and `finished_at` for each run.
- `.pse-generated.json` records hashes for files owned by the generator. Normal generation refreshes owned files and removes stale owned output.
- `pse --no-overwrite ...` preserves user-modified generated files while still refreshing unchanged owned files.
- Controllers are intentionally thin and call Application services, or dispatch CQRS messages when CQRS is enabled.
- Database projects receive EF Core repositories backed by `AppDbContext`; projects without a database receive thread-safe in-memory repositories.
- Test classes contain runnable construction and property assertions and can be extended with domain behavior tests.

### Running

Run the generator through the installed CLI:

```bash
pse sample_with_capabilities.pse -o ./sample_output
```

Or through the registered textX generator:

```bash
textx generate pse/sample_with_capabilities.pse --target dotnet -o ./sample_output --overwrite
```

Use `pse sample_with_capabilities.pse -o ./sample_output --no-overwrite` when generated files contain edits that must be preserved.

---

## Core Principles

### Architecture First

The DSL describes architecture rather than implementation details.

Avoid:

```text
package MediatR
package AutoMapper
```

Prefer:

```text
Capability CQRS
Capability Validation
Capability Mapping
```

The heuristics engine resolves capabilities to technologies.

### Technology Agnostic

Technologies are selected through presets and registries.

Today:

```yaml
cqrs: mediatr
```

Tomorrow:

```yaml
cqrs: wolverine
```

No DSL changes required.

### Convention Over Configuration

Reasonable defaults should generate a working project with minimal configuration.

Example:

```text
Project StoreApi {
    Archetype WebApi
}
```

May automatically generate:

* ASP.NET Core Web API
* PostgreSQL
* Docker
* GitHub Actions
* Logging
* Validation
* Testing
* Health Checks

Based on configured heuristics.

---

## Archetypes

Archetypes define high-level project structures.

### WebApi

```text
Presentation
Application
Domain
Infrastructure
Tests
```

### CleanArchitecture

```text
Presentation
Application
Domain
Infrastructure
```

Other archetypes should only be added when their generated solution is covered by the same build matrix.

---

## Domain Modeling

PSE supports modeling of:

* Entities
* Value Objects
* Aggregates
* Domain Events
* Repositories
* Bounded Contexts

Example:

```text
Context Identity {

    Entity User {
        Guid Id
        Email Email
    }

    ValueObject Email

    Aggregate UserAggregate {
        Root User
    }
}
```

Generated artifacts may include:

* Domain entities
* Repository interfaces
* DTOs
* CQRS handlers
* Validation rules

---

## Infrastructure Modeling

Infrastructure is described declaratively.

Example:

```text
Infrastructure {

    Database PostgreSQL

    Cache Redis

    MessageBroker RabbitMQ

    ObjectStorage MinIO
}
```

PSE generates deployment artifacts automatically.

### Docker

```yaml
docker-compose.yml
```

### Kubernetes

```yaml
deploy/kubernetes/namespace.yaml
deploy/kubernetes/manifest.yaml
deploy/kubernetes/secret.example.yaml
```

### Docker Swarm

```yaml
deploy/swarm/stack.yml
deploy/swarm/README.md
```

`secret.example.yaml` is never applied by the generated Kubernetes instructions. Supply real secrets using the cluster's secret-management workflow. Swarm secrets are declared as external and must be created before stack deployment.

---

## Deployment Targets

```text
Deployment Docker
```

```text
Deployment Kubernetes
```

```text
Deployment DockerSwarm
```

The same architecture model can produce different deployment artifacts.

---

## Heuristics Engine

The heuristics engine applies organizational standards and best practices.

Example:

```text
Project StoreApi {
    Archetype WebApi
}
```

May resolve to:

```yaml
logging: serilog
validation: fluentvalidation
database: postgres
testing: xunit
deployment: docker
```

All decisions are configurable.

---

## Registries

### Version Registry

```yaml
versions:

  dotnet: 9.0
  postgres: 17
  redis: 8
```

### Package Registry

```yaml
mediatr:
  package: MediatR
  version: 13.0.0
```

### Preset Registry

```yaml
webapi:
  logging: serilog
  validation: fluentvalidation
  cqrs: mediatr
```

---

## Repository Structure

```text
pse/

├── grammar/
│   └── pse.tx
│
├── model/
│   └── architecture.py
│
├── heuristics/
│   ├── archetypes.yaml
│   ├── presets.yaml
│   ├── packages.yaml
│   └── versions.yaml
│
├── validators/
│
├── generators/
│   ├── dotnet/
│   ├── java/
│   ├── docker/
│   ├── kubernetes/
│   └── github_actions/
│
├── templates/
│
└── tests/
```

## License

MIT
