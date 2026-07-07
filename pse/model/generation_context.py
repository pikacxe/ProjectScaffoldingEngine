from dataclasses import dataclass, field
from typing import Any, Dict, Optional

from pse.model.architecture import ArchitectureModel


@dataclass
class GenerationContext:
    architecture: ArchitectureModel
    output_dir: str

    # registries / heuristics
    presets: Dict[str, Any] = field(default_factory=dict)
    packages: Dict[str, Any] = field(default_factory=dict)
    versions: Dict[str, Any] = field(default_factory=dict)

    # runtime options
    options: Dict[str, Any] = field(default_factory=dict)

    # logging hook (optional but useful later)
    log: callable = print
