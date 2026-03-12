# Project Scaffolding Engine

PSE uses textX (a Python DSL framework) to define and generate standardized .NET projects following Domain-Driven Design (DDD). It supports multi-language targets (e.g., Java), Docker/Docker Compose, git repos, package dependencies, naming conventions, and GitHub Actions CI/CD workflows.

### Quick Start

Install
```bash
pip install textX[cli] textX-jinja
```
### Usage

- Save grammar as projectx.tx.

- Write your project as myproj.projx.

- Generate: textx generate myproj.projx dotnet --output-dir ./output.

### Grammar (projectx.tx)

```text
Project: 'Project' name=ID target=('dotnet'|'java')? '{'
         projects*=SubProject
         packages*=Package
         docker?=Docker
         compose?=Compose
         ci?=CI
         git?=GitRepo
       '}' ;

SubProject: layer=ID name=ID '{' folders*=[ID] '}' ;
Package: 'package' name=ID version=VERSION ;
Docker: 'docker' image=STRING ports*=[INT:INT] volumes*=[STRING:STRING] ;
Compose: 'compose' '{' services*=[Service] '}' ;
Service: name=ID image=STRING? ports*=[INT:INT] depends*=[ID] env*=[ID:STRING] ;
CI: 'ci' triggers*=['push'|'pull_request'] jobs*=[Job] ;
Job: name=ID steps*=[Step] ;
Step: name=ID cmd=STRING ;
GitRepo: 'git' url=STRING ('init')? branch=ID? ;

```
### Sample DSL (example.pse)

```text
Project MySolution target=dotnet {
  Domain: Core { Entities, ValueObjects, Repositories }
  Application: Services { UseCases, DTOs }
  Infrastructure: Api { Controllers, Middleware }
  
  package MediatR 12.0.1
  package AutoMapper 12.0.1
  
  docker image="mcr.microsoft.com/dotnet/sdk:8.0" 
         ports=[8080:80] 
         volumes=["./app:/app", "./logs:/logs"];
  
  compose {
    api name=api image="myapi" ports=[8080:80] depends=[db];
    db name=db image="postgres:15" volumes=["./pgdata:/var/lib/postgresql/data"];
  }
  
  ci triggers=['push','pull_request'] {
    build name=build steps=[
      name=restore cmd="dotnet restore",
      name=build cmd="dotnet build --no-restore"
    ];
    test name=test steps=[
      name=tests cmd="dotnet test --no-build --verbosity normal"
    ];
  }
  
  git "https://github.com/myorg/mysol" init main
}

```
### Generators

.NET Generator Example (generators/dotnet_generator.py)
```python
from textx import metamodel_from_file
from textxjinja import textx_jinja_generator
import subprocess
import os

def generate_dotnet(metamodel, model, output_path, overwrite=True):
    context = {'model': model}
    textx_jinja_generator('templates/dotnet', output_path, context, overwrite)
    
    os.chdir(output_path)
    subprocess.run(["dotnet", "new", "sln", "-n", model.name])
    
    for proj in model.projects:
        proj_path = f"{proj.layer}.{proj.name}"
        subprocess.run(["dotnet", "new", "classlib", "-o", proj_path])
        subprocess.run(["dotnet", "sln", "add", proj_path])
    
    # Add packages to first project (or make configurable)
    target_proj = model.projects[0].layer + "." + model.projects[0].name
    for pkg in model.packages:
        subprocess.run(["dotnet", "add", target_proj, "package", f"{pkg.name}"])
    
    subprocess.run(["git", "init"])
    if model.git:
        subprocess.run(["git", "remote", "add", "origin", model.git.url])
        if model.git.init and model.git.branch:
            subprocess.run(["git", "checkout", "-b", model.git.branch])

mm = metamodel_from_file('projectx.tx')
mm.register_generator('dotnet', generate_dotnet)

```
#### Java Generator

Swap target=java in DSL; generate Maven/Gradle, OpenJDK Dockerfile. (TODO)

### Templates Folder Structure

```text
templates/dotnet/
├── Dockerfile.j2                    # FROM {{ model.docker.image }}
├── docker-compose.yml.j2           # volumes: "{{ svc.volumes[0] }}"
├── {{ model.name }}.sln.j2
├── .github/workflows/ci.yml.j2     # GitHub Actions
└── {{ layer }}.{{ name }}/{{ name }}.csproj.j2# Project Scaffolding Engine (PSE)
```

### .github/workflows/ci.yml.j2 - example

```text
name: CI
on: [{% for t in model.ci.triggers %}{{t}},{% endfor %}]
jobs:
{% for job in model.ci.jobs %}
  {{ job.name }}:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v4
    {% for step in job.steps %}
    - name: {{ step.name }}
      run: {{ step.cmd }}
    {% endfor %}
{% endfor %}


```

### Features

- DDD Layers: Auto-folders (Domain, App, Infra) with naming rules.

- Multi-Target: Switch target=java → pom.xml, Gradle.

- Docker: Dynamic Dockerfile/Compose from DSL ports/volumes/services.

- Git: Init + remote setup.

- Extensible: Add CI/CD, tests, validators via grammar rules/processors.

### Testing

```bash
textx check example.pse
textx parse example.pse --py-ast
```

### License
[MIT](https://github.com/pikacxe/ProjectScaffoldingEngine/blob/main/LICENSE)
