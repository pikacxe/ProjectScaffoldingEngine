from dataclasses import dataclass, field
from typing import Dict, List


@dataclass
class DependencyGraph:
    nodes: Dict[str, List[str]] = field(default_factory=dict)


    def add(self, node: str, depends_on: List[str]):
        self.nodes[node] = depends_on


    def topological_sort(self):
        visited = set()
        result = []

        def visit(n):
            if n in visited:
                return
            visited.add(n)

            for dep in self.nodes.get(n, []):
                visit(dep)

            result.append(n)

        for node in self.nodes:
            visit(node)

        return result