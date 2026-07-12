import os

from pse.template_loader import render_template

from .common import DeploymentSpec, write_text, write_yaml
from .dockerfile import write_dockerfile


def create_swarm_deployment(ctx):
    spec = DeploymentSpec.from_context(ctx)
    write_dockerfile(ctx, spec)

    services = {spec.app_name: app_service(spec)}
    volumes = {}
    secrets = {}

    if spec.has_database:
        services["postgres"] = postgres_service(spec)
        volumes["postgres-data"] = {}
        secrets["postgres-password"] = {"external": True}
        secrets["database-connection"] = {"external": True}
    if spec.has_cache:
        services["redis"] = redis_service(spec)
        volumes["redis-data"] = {}
        secrets["redis-connection"] = {"external": True}
    if spec.has_broker:
        services["rabbitmq"] = rabbitmq_service(spec)
        volumes["rabbitmq-data"] = {}
        secrets["rabbitmq-connection"] = {"external": True}
        secrets["rabbitmq-password"] = {"external": True}

    document = {
        "services": services,
        "networks": {"backend": {"driver": "overlay", "attachable": True}},
    }
    if volumes:
        document["volumes"] = volumes
    if secrets:
        document["secrets"] = secrets

    deploy_dir = os.path.join(ctx.output_dir, "deploy", "swarm")
    write_yaml(os.path.join(deploy_dir, "stack.yml"), document)
    write_text(os.path.join(deploy_dir, "README.md"), swarm_readme(spec))


def app_service(spec):
    service = {
        "image": spec.image,
        "environment": {
            "ASPNETCORE_ENVIRONMENT": "Production",
            "ASPNETCORE_URLS": "http://+:8080",
        },
        "ports": [{"target": 8080, "published": 8080, "protocol": "tcp", "mode": "ingress"}],
        "networks": ["backend"],
        "deploy": {
            "replicas": 2,
            "update_config": {"parallelism": 1, "delay": "10s", "order": "start-first"},
            "rollback_config": {"parallelism": 1, "order": "stop-first"},
            "restart_policy": {"condition": "on-failure", "delay": "5s", "max_attempts": 3},
            "resources": {
                "limits": {"cpus": "1.0", "memory": "512M"},
                "reservations": {"cpus": "0.25", "memory": "128M"},
            },
        },
        "healthcheck": {
            "test": ["CMD", "curl", "--fail", "--silent", "http://localhost:8080/health/live"],
            "interval": "30s",
            "timeout": "5s",
            "retries": 3,
            "start_period": "15s",
        },
    }
    secret_names = []
    if spec.has_database:
        secret_names.append("database-connection")
    if spec.has_cache:
        secret_names.append("redis-connection")
    if spec.has_broker:
        secret_names.append("rabbitmq-connection")
    if secret_names:
        service["secrets"] = [
            {"source": name, "target": secret_target(name)}
            for name in secret_names
        ]
    return service


def postgres_service(spec):
    return {
        "image": f"postgres:{spec.postgres_version}",
        "environment": {
            "POSTGRES_DB": "app",
            "POSTGRES_USER": "postgres",
            "POSTGRES_PASSWORD_FILE": "/run/secrets/postgres-password",
        },
        "secrets": ["postgres-password"],
        "volumes": ["postgres-data:/var/lib/postgresql/data"],
        "networks": ["backend"],
        "healthcheck": {
            "test": ["CMD-SHELL", "pg_isready -U postgres -d app"],
            "interval": "10s",
            "timeout": "5s",
            "retries": 5,
        },
        "deploy": {"replicas": 1, "restart_policy": {"condition": "on-failure"}},
    }


def redis_service(spec):
    return {
        "image": f"redis:{spec.redis_version}",
        "command": ["redis-server", "--appendonly", "yes"],
        "volumes": ["redis-data:/data"],
        "networks": ["backend"],
        "healthcheck": {
            "test": ["CMD", "redis-cli", "ping"],
            "interval": "10s",
            "timeout": "5s",
            "retries": 5,
        },
        "deploy": {"replicas": 1, "restart_policy": {"condition": "on-failure"}},
    }


def rabbitmq_service(spec):
    return {
        "image": f"rabbitmq:{spec.rabbitmq_version}",
        "environment": {
            "RABBITMQ_DEFAULT_USER": "app",
            "RABBITMQ_DEFAULT_PASS_FILE": "/run/secrets/rabbitmq-password",
        },
        "secrets": ["rabbitmq-password"],
        "volumes": ["rabbitmq-data:/var/lib/rabbitmq"],
        "networks": ["backend"],
        "healthcheck": {
            "test": ["CMD", "rabbitmq-diagnostics", "-q", "ping"],
            "interval": "10s",
            "timeout": "5s",
            "retries": 5,
        },
        "deploy": {"replicas": 1, "restart_policy": {"condition": "on-failure"}},
    }


def secret_target(name):
    return {
        "database-connection": "ConnectionStrings__Database",
        "redis-connection": "ConnectionStrings__Redis",
        "rabbitmq-connection": "ConnectionStrings__RabbitMq",
    }[name]


def swarm_readme(spec):
    commands = []
    if spec.has_database:
        commands.extend([
            "printf '%s' 'replace-me' | docker secret create postgres-password -",
            "printf '%s' 'Host=postgres;Port=5432;Database=app;Username=postgres;Password=replace-me' | docker secret create database-connection -",
        ])
    if spec.has_cache:
        commands.append("printf '%s' 'redis:6379' | docker secret create redis-connection -")
    if spec.has_broker:
        commands.extend([
            "printf '%s' 'replace-me' | docker secret create rabbitmq-password -",
            "printf '%s' 'amqp://app:replace-me@rabbitmq:5672' | docker secret create rabbitmq-connection -",
        ])

    secret_block = "\n".join(commands) or "# No infrastructure secrets are required."
    return render_template(
        "deployment/swarm-readme.md.tmpl",
        {
            "Image": spec.image,
            "SecretCommands": secret_block,
            "AppName": spec.app_name,
        },
    )
