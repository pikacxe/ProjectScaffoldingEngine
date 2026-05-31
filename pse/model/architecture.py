from dataclasses import dataclass, field
from typing import List, Dict, Optional


@dataclass
class Project:
    name: str
    archetype: str
    target: str


@dataclass
class Entity:
    name: str
    properties: Dict[str, str]


@dataclass
class ValueObject:
    name: str
    properties: Dict[str, str]


@dataclass
class Aggregate:
    name: str
    root: str
    children: List[str]


@dataclass
class Context:
    name: str
    entities: List[Entity] = field(default_factory=list)
    value_objects: List[ValueObject] = field(default_factory=list)
    aggregates: List[Aggregate] = field(default_factory=list)


@dataclass
class Database:
    type: str
    version: Optional[str] = None


@dataclass
class Cache:
    type: str


@dataclass
class MessageBroker:
    type: str


@dataclass
class Infrastructure:
    database: Optional[Database] = None
    cache: Optional[Cache] = None
    broker: Optional[MessageBroker] = None


@dataclass
class Deployment:
    target: str


@dataclass
class ArchitectureModel:
    project: Project
    contexts: List[Context]
    infrastructure: Infrastructure
    deployment: Deployment
    capabilities: List[str] = field(default_factory=list)