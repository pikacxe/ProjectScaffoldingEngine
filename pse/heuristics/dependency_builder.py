import os

import yaml

from pse.model.dependency_graph import DependencyGraph


HEURISTICS_DIR = os.path.dirname(__file__)


def build_dependency_graph(capability_graph):
    with open(os.path.join(HEURISTICS_DIR, "capabilities.yaml"), "r", encoding="utf-8") as f:
        registry = yaml.safe_load(f)

    graph = DependencyGraph()

    for cap_name, cap in capability_graph.capabilities.items():

        implementation = cap.value

        meta = registry.get(cap_name, {}).get(implementation, {})

        depends_on = meta.get("depends_on", [])

        graph.add(cap_name, depends_on)

    return graph
