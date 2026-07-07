import unittest

from pse.model.dependency_graph import DependencyCycleError, DependencyGraph


class DependencyGraphTests(unittest.TestCase):
    def test_topological_sort_orders_dependencies_first(self):
        graph = DependencyGraph()
        graph.add("api", ["domain"])
        graph.add("domain", [])

        self.assertEqual(graph.topological_sort(), ["domain", "api"])

    def test_topological_sort_rejects_cycles(self):
        graph = DependencyGraph()
        graph.add("a", ["b"])
        graph.add("b", ["a"])

        with self.assertRaises(DependencyCycleError):
            graph.topological_sort()


if __name__ == "__main__":
    unittest.main()
