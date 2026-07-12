import os

from pse.template_loader import render_template

from .common import DeploymentSpec, labels, write_text, write_yaml_documents
from .dockerfile import write_dockerfile


def create_kubernetes_deployment(ctx):
    spec = DeploymentSpec.from_context(ctx)
    write_dockerfile(ctx, spec)
    documents = [app_deployment(spec), app_service(spec)]

    if spec.has_database:
        documents.extend([postgres_service(spec), postgres_stateful_set(spec)])
    if spec.has_cache:
        documents.extend([redis_service(spec), redis_stateful_set(spec)])
    if spec.has_broker:
        documents.extend([rabbitmq_service(spec), rabbitmq_stateful_set(spec)])

    deploy_dir = os.path.join(ctx.output_dir, "deploy", "kubernetes")
    write_yaml_documents(os.path.join(deploy_dir, "namespace.yaml"), [namespace(spec)])
    if spec.has_database or spec.has_cache or spec.has_broker:
        write_yaml_documents(os.path.join(deploy_dir, "secret.example.yaml"), [app_secret(spec)])
    write_yaml_documents(os.path.join(deploy_dir, "manifest.yaml"), documents)
    write_text(os.path.join(deploy_dir, "README.md"), kubernetes_readme(spec))


def namespace(spec):
    return {
        "apiVersion": "v1",
        "kind": "Namespace",
        "metadata": {"name": spec.app_name, "labels": labels(spec, "platform")},
    }


def app_secret(spec):
    string_data = {}
    if spec.has_database:
        string_data["database-connection"] = "Host=postgres;Port=5432;Database=app;Username=postgres;Password=change-me"
        string_data["postgres-password"] = "change-me"
    if spec.has_cache:
        string_data["redis-connection"] = "redis:6379"
    if spec.has_broker:
        string_data["rabbitmq-connection"] = "amqp://app:change-me@rabbitmq:5672"
        string_data["rabbitmq-password"] = "change-me"
    return {
        "apiVersion": "v1",
        "kind": "Secret",
        "metadata": {"name": f"{spec.app_name}-secrets", "namespace": spec.app_name, "labels": labels(spec, "configuration")},
        "type": "Opaque",
        "stringData": string_data,
    }


def app_deployment(spec):
    pod_labels = labels(spec, "api")
    env = [
        {"name": "ASPNETCORE_ENVIRONMENT", "value": "Production"},
        {"name": "ASPNETCORE_URLS", "value": "http://+:8080"},
    ]
    for enabled, env_name, key in (
        (spec.has_database, "ConnectionStrings__Database", "database-connection"),
        (spec.has_cache, "ConnectionStrings__Redis", "redis-connection"),
        (spec.has_broker, "ConnectionStrings__RabbitMq", "rabbitmq-connection"),
    ):
        if enabled:
            env.append(secret_env(spec, env_name, key))

    return {
        "apiVersion": "apps/v1",
        "kind": "Deployment",
        "metadata": {"name": spec.app_name, "namespace": spec.app_name, "labels": pod_labels},
        "spec": {
            "replicas": 2,
            "strategy": {"type": "RollingUpdate", "rollingUpdate": {"maxUnavailable": 0, "maxSurge": 1}},
            "selector": {"matchLabels": {"app.kubernetes.io/name": spec.app_name, "app.kubernetes.io/component": "api"}},
            "template": {
                "metadata": {"labels": pod_labels},
                "spec": {
                    "securityContext": {"runAsNonRoot": True, "seccompProfile": {"type": "RuntimeDefault"}},
                    "containers": [{
                        "name": "api",
                        "image": spec.image,
                        "imagePullPolicy": "IfNotPresent",
                        "ports": [{"name": "http", "containerPort": 8080}],
                        "env": env,
                        "readinessProbe": http_probe("/health/ready", 5),
                        "livenessProbe": http_probe("/health/live", 15),
                        "resources": {
                            "requests": {"cpu": "100m", "memory": "128Mi"},
                            "limits": {"cpu": "1000m", "memory": "512Mi"},
                        },
                        "securityContext": {
                            "allowPrivilegeEscalation": False,
                            "readOnlyRootFilesystem": True,
                            "capabilities": {"drop": ["ALL"]},
                        },
                        "volumeMounts": [{"name": "tmp", "mountPath": "/tmp"}],
                    }],
                    "volumes": [{"name": "tmp", "emptyDir": {}}],
                },
            },
        },
    }


def app_service(spec):
    return service_document(spec, spec.app_name, "api", 80, 8080)


def postgres_service(spec):
    return service_document(spec, "postgres", "postgres", 5432, 5432, headless=True)


def redis_service(spec):
    return service_document(spec, "redis", "redis", 6379, 6379, headless=True)


def rabbitmq_service(spec):
    return service_document(spec, "rabbitmq", "rabbitmq", 5672, 5672, headless=True)


def service_document(spec, name, component, port, target_port, headless=False):
    document = {
        "apiVersion": "v1",
        "kind": "Service",
        "metadata": {"name": name, "namespace": spec.app_name, "labels": labels(spec, component)},
        "spec": {
            "selector": {"app.kubernetes.io/name": spec.app_name, "app.kubernetes.io/component": component},
            "ports": [{"name": "tcp", "port": port, "targetPort": target_port}],
        },
    }
    if headless:
        document["spec"]["clusterIP"] = "None"
    return document


def postgres_stateful_set(spec):
    return stateful_set(
        spec,
        "postgres",
        f"postgres:{spec.postgres_version}",
        5432,
        [
            {"name": "POSTGRES_DB", "value": "app"},
            {"name": "POSTGRES_USER", "value": "postgres"},
            {"name": "PGDATA", "value": "/var/lib/postgresql/data/pgdata"},
            secret_env(spec, "POSTGRES_PASSWORD", "postgres-password"),
        ],
        ["CMD-SHELL", "pg_isready -U postgres -d app"],
        "/var/lib/postgresql/data",
    )


def redis_stateful_set(spec):
    return stateful_set(
        spec,
        "redis",
        f"redis:{spec.redis_version}",
        6379,
        [],
        ["CMD", "redis-cli", "ping"],
        "/data",
        command=["redis-server", "--appendonly", "yes"],
    )


def rabbitmq_stateful_set(spec):
    return stateful_set(
        spec,
        "rabbitmq",
        f"rabbitmq:{spec.rabbitmq_version}",
        5672,
        [
            {"name": "RABBITMQ_DEFAULT_USER", "value": "app"},
            secret_env(spec, "RABBITMQ_DEFAULT_PASS", "rabbitmq-password"),
        ],
        ["CMD", "rabbitmq-diagnostics", "-q", "ping"],
        "/var/lib/rabbitmq",
    )


def stateful_set(spec, name, image, port, env, readiness_command, mount_path, command=None):
    pod_labels = labels(spec, name)
    container = {
        "name": name,
        "image": image,
        "ports": [{"name": "tcp", "containerPort": port}],
        "env": env,
        "readinessProbe": {
            "exec": {"command": readiness_command},
            "initialDelaySeconds": 5,
            "periodSeconds": 10,
        },
        "resources": {
            "requests": {"cpu": "100m", "memory": "128Mi"},
            "limits": {"cpu": "500m", "memory": "512Mi"},
        },
        "securityContext": {"allowPrivilegeEscalation": False, "capabilities": {"drop": ["ALL"]}},
        "volumeMounts": [{"name": "data", "mountPath": mount_path}],
    }
    if command:
        container["command"] = command

    return {
        "apiVersion": "apps/v1",
        "kind": "StatefulSet",
        "metadata": {"name": name, "namespace": spec.app_name, "labels": pod_labels},
        "spec": {
            "serviceName": name,
            "replicas": 1,
            "selector": {"matchLabels": {"app.kubernetes.io/name": spec.app_name, "app.kubernetes.io/component": name}},
            "template": {
                "metadata": {"labels": pod_labels},
                "spec": {"containers": [container]},
            },
            "volumeClaimTemplates": [{
                "metadata": {"name": "data"},
                "spec": {
                    "accessModes": ["ReadWriteOnce"],
                    "resources": {"requests": {"storage": "1Gi"}},
                },
            }],
        },
    }


def secret_env(spec, name, key):
    return {
        "name": name,
        "valueFrom": {"secretKeyRef": {"name": f"{spec.app_name}-secrets", "key": key}},
    }


def http_probe(path, initial_delay):
    return {
        "httpGet": {"path": path, "port": "http"},
        "initialDelaySeconds": initial_delay,
        "periodSeconds": 10,
        "timeoutSeconds": 3,
        "failureThreshold": 3,
    }


def kubernetes_readme(spec):
    secret_setup = ""
    if spec.has_database or spec.has_cache or spec.has_broker:
        secret_setup = (
            f"\n{secret_command(spec)}\n"
        )

    return render_template(
        "deployment/kubernetes-readme.md.tmpl",
        {
            "Image": spec.image,
            "SecretSetup": secret_setup,
            "AppName": spec.app_name,
        },
    )


def secret_command(spec):
    literals = []
    if spec.has_database:
        literals.extend([
            "--from-literal=database-connection='replace-me'",
            "--from-literal=postgres-password='replace-me'",
        ])
    if spec.has_cache:
        literals.append("--from-literal=redis-connection='redis:6379'")
    if spec.has_broker:
        literals.extend([
            "--from-literal=rabbitmq-connection='replace-me'",
            "--from-literal=rabbitmq-password='replace-me'",
        ])

    return (
        f"kubectl -n {spec.app_name} create secret generic {spec.app_name}-secrets \\\n"
        + " \\\n".join(f"  {literal}" for literal in literals)
    )
