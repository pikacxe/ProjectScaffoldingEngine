import pathlib
import subprocess
import sys
import tempfile
import unittest


ROOT = pathlib.Path(__file__).resolve().parents[1]


class BootstrapCliTests(unittest.TestCase):
    def test_invalid_dsl_exits_nonzero(self):
        source = """Project StoreApi target=dotnet {
    Archetype WebApi
    Capabilities {
        Capability UnknownCapability
    }
}"""

        with tempfile.TemporaryDirectory() as temp_dir:
            dsl_path = pathlib.Path(temp_dir) / "invalid.pse"
            dsl_path.write_text(source, encoding="utf-8")

            result = subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "pse.run",
                    str(dsl_path),
                    "-o",
                    str(pathlib.Path(temp_dir) / "output"),
                ],
                cwd=ROOT,
                text=True,
                capture_output=True,
            )

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("Capability 'UnknownCapability' is not recognized", result.stdout)


if __name__ == "__main__":
    unittest.main()
