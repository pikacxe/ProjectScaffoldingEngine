from dataclasses import dataclass, field
from typing import Dict


@dataclass
class Capability:
    name: str
    value: str
    source: str


@dataclass
class CapabilityGraph:
    capabilities: Dict[str, Capability] = field(default_factory=dict)