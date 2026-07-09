import pathlib
import unittest

import yaml


ROOT = pathlib.Path(__file__).resolve().parents[1]
HEURISTICS = ROOT / "pse" / "heuristics"


class HeuristicsTests(unittest.TestCase):
    def load(self, name):
        with (HEURISTICS / name).open(encoding="utf-8") as handle:
            return yaml.safe_load(handle) or {}

    def test_package_version_keys_exist(self):
        packages = self.load("packages.yaml")
        versions = self.load("versions.yaml")

        missing = []
        for implementation, config in packages.items():
            for package in config.get("packages", []):
                if isinstance(package, dict):
                    version = package.get("version")
                    if version and version not in versions:
                        missing.append(f"{implementation}:{package.get('name')} -> {version}")

        self.assertEqual(missing, [])

    def test_capability_implementations_have_package_entries(self):
        capabilities = self.load("capabilities.yaml")
        packages = self.load("packages.yaml")

        missing = []
        for implementations in capabilities.values():
            for implementation in implementations:
                if implementation not in packages:
                    missing.append(implementation)

        self.assertEqual(missing, [])

    def test_advertised_capabilities_are_generator_supported(self):
        capabilities = set(self.load("capabilities.yaml"))
        supported = {
            "validation",
            "logging",
            "mapping",
            "cqrs",
            "testing",
            "database",
            "cache",
            "messaging",
        }

        self.assertEqual(capabilities - supported, set())


if __name__ == "__main__":
    unittest.main()
