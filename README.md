# Project Scaffolding Engine (PSE)

PSE is a Domain-Driven Design (DDD) architecture scaffolding engine built on top of textX.

Instead of generating folders and files directly, PSE allows developers to describe software architecture using a domain-specific language (DSL). The engine applies architectural heuristics, technology presets, and generation plugins to produce production-ready project structures.

The goal is to provide a consistent, maintainable starting point for modern software projects while remaining technology-agnostic and future-proof.

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
* Docker configurations
* CI/CD pipelines
* Infrastructure manifests
* Documentation
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
- Constructs: Project, Archetype, Contexts, Entities, ValueObjects, Aggregates, Infrastructure, Deployment.
- No packages/frameworks/CI/CD in DSL; intent only.

**Architecture Model (Core IR)**

- Normalized `ArchitectureModel` with project metadata, contexts, entities, value objects, aggregates, infrastructure, and deployment.
- Decouples DSL from generators and enables multi-language targets.

**Heuristics System (Externalized Intelligence)**

- YAML registries: `archetypes.yaml`, `presets.yaml`, `packages.yaml`, `versions.yaml`, `capabilities.yaml`.
- Maps archetypes to capabilities, capabilities to implementations, implementations to packages and versions.

**Bootstrap System (Execution Orchestrator)**

- Validates environment, loads grammar, parses DSL, builds `ArchitectureModel`, loads heuristics.
- Builds `GenerationContext` and dispatches generators.
- Fail-fast, deterministic execution flow.
- Writes a run manifest (`pse.manifest.json`) with DSL input, resolved capabilities, timestamps, and status.

**GenerationContext (Unified Generator Contract)**

- Shared contract for all generators: architecture model, heuristics, output path, options, logging.
- Removes direct dependency on textX models in generators.

**Dotnet Generator (Pipeline-Based)**

```text
generate_dotnet(ctx)
    ├── create_solution()
    ├── create_projects()
    ├── restore_packages()
    └── create_docker()
```

**Docker Generation (Basic Infrastructure Output)**

- Dockerfile generation and runtime image wiring.
- Tied to deployment target in the architecture model.

**Capability System + Resolver (Major Milestone)**

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
- Infrastructure scaling (Docker now, Kubernetes next).
- Archetype evolution (Clean Architecture, Modular Monolith, Microservices).

### Next Milestone

The missing brain layer is package resolution and conflict solving:

- Capability-to-package mapping.
- Version conflict resolution.
- Dependency collision handling.
- Project-level `csproj` composition.
- Transitive dependency reasoning.

### DSL

The DSL describes architecture and business requirements.

Example:

```text
Project StoreApi target=dotnet {

    Archetype WebApi

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

### ModularMonolith

```text
Modules
 ├── Identity
 ├── Orders
 └── Billing
```

### Microservices

```text
Services
Gateway
Shared
Infrastructure
```

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
deployments/
services/
configmaps/
```

### Future Targets

* Docker Compose
* Kubernetes
* Docker Swarm
* Nomad

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

## Plugin System

PSE is built around generator plugins.

```text
plugins/

├── dotnet
├── java
├── docker
├── kubernetes
├── github_actions
├── terraform
```

A plugin may provide:

* Grammar extensions
* Validators
* Templates
* Generators

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

---

## Roadmap

### Phase 1

* DSL foundation
* Architecture model
* .NET generator
* Docker generator
* Git integration

### Phase 2

* Domain modeling
* API generation
* Validation engine
* GitHub Actions

### Phase 3

* Kubernetes support
* Terraform support
* Java generator
* Multi-service architectures

---

## License

MIT
