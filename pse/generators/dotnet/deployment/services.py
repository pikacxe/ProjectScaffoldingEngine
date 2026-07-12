def app_environment(spec):
    environment = {
        "ASPNETCORE_ENVIRONMENT": "Production",
        "ASPNETCORE_URLS": "http://+:8080",
    }
    if spec.has_database:
        environment["ConnectionStrings__Database"] = (
            "Host=postgres;Port=5432;Database=app;Username=postgres;Password=postgres"
        )
    if spec.has_cache:
        environment["ConnectionStrings__Redis"] = "redis:6379"
    if spec.has_broker:
        environment["ConnectionStrings__RabbitMq"] = "amqp://app:rabbitmq@rabbitmq:5672"
    return environment


def compose_dependencies(spec):
    services = {}
    volumes = {}

    if spec.has_database:
        services["postgres"] = {
            "image": f"postgres:{spec.postgres_version}",
            "environment": {
                "POSTGRES_DB": "app",
                "POSTGRES_USER": "postgres",
                "POSTGRES_PASSWORD": "postgres",
            },
            "healthcheck": {
                "test": ["CMD-SHELL", "pg_isready -U postgres -d app"],
                "interval": "10s",
                "timeout": "5s",
                "retries": 5,
            },
            "volumes": ["postgres-data:/var/lib/postgresql/data"],
            "networks": ["backend"],
        }
        volumes["postgres-data"] = {}

    if spec.has_cache:
        services["redis"] = {
            "image": f"redis:{spec.redis_version}",
            "command": ["redis-server", "--appendonly", "yes"],
            "healthcheck": {
                "test": ["CMD", "redis-cli", "ping"],
                "interval": "10s",
                "timeout": "5s",
                "retries": 5,
            },
            "volumes": ["redis-data:/data"],
            "networks": ["backend"],
        }
        volumes["redis-data"] = {}

    if spec.has_broker:
        services["rabbitmq"] = {
            "image": f"rabbitmq:{spec.rabbitmq_version}",
            "environment": {
                "RABBITMQ_DEFAULT_USER": "app",
                "RABBITMQ_DEFAULT_PASS": "rabbitmq",
            },
            "healthcheck": {
                "test": ["CMD", "rabbitmq-diagnostics", "-q", "ping"],
                "interval": "10s",
                "timeout": "5s",
                "retries": 5,
            },
            "volumes": ["rabbitmq-data:/var/lib/rabbitmq"],
            "networks": ["backend"],
        }
        volumes["rabbitmq-data"] = {}

    return services, volumes
