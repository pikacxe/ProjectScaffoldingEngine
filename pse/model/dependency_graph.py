from dataclasses import dataclass, field
from typing import Dict, List


class DependencyCycleError(ValueError):
    pass


@dataclass
class DependencyGraph:
    nodes: Dict[str, List[str]] = field(default_factory=dict)

    def add(self, node: str, depends_on: List[str]):
        self.nodes[node] = depends_on

    def topological_sort(self):
        visited = set()
        visiting = set()
        result = []

        def visit(n):
            if n in visiting:
                cycle = " -> ".join([*visiting, n])
                raise DependencyCycleError(f"Dependency cycle detected: {cycle}")

            if n in visited:
                return

            visiting.add(n)

            for dep in self.nodes.get(n, []):
                visit(dep)

            visiting.remove(n)
            visited.add(n)
            result.append(n)

        for node in self.nodes:
            visit(node)

        return result
