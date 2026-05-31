from model.architecture import (
    ArchitectureModel,
    Project,
    Context,
    Entity,
    ValueObject,
    Aggregate,
    Infrastructure,
    Database,
    Cache,
    MessageBroker,
    Deployment
)


def map_model_to_architecture(model):

    return ArchitectureModel(
        project=Project(
            name=model.name,
            archetype=model.archetype.value,
            target=model.target or "dotnet"
        ),
        contexts=[
            Context(
                name=c.name,
                entities=[
                    Entity(
                        name=e.name,
                        properties={p.name: p.type for p in e.properties}
                    )
                    for e in c.entities
                ],
                value_objects=[
                    ValueObject(
                        name=v.name,
                        properties={p.name: p.type for p in v.properties}
                    )
                    for v in c.valueObjects
                ],
                aggregates=[
                    Aggregate(
                        name=a.name,
                        root=a.root.name if a.root else None,
                        children=[c.name for c in a.children]
                    )
                    for a in c.aggregates
                ]
            )
            for c in model.contexts
        ],
        infrastructure=map_infra(model.infrastructure),
        deployment=map_deployment(model.deployment)
    )


def map_infra(infra):
    if not infra:
        return None

    return Infrastructure(
        database=Database(infra.database.type) if infra.database else None,
        cache=Cache(infra.cache.type) if infra.cache else None,
        broker=MessageBroker(infra.broker.type) if infra.broker else None
    )


def map_deployment(dep):
    if not dep:
        return None

    return Deployment(target=dep.target)