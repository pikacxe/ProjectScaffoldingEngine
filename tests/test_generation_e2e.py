import os
import pathlib
import shutil
import subprocess
import tempfile
import unittest

from pse.bootstrap import run_pse


ROOT = pathlib.Path(__file__).resolve().parents[1]
RUN_E2E = os.environ.get("PSE_RUN_E2E") == "1"


@unittest.skipUnless(RUN_E2E and shutil.which("dotnet"), "set PSE_RUN_E2E=1 to run generation builds")
class GenerationMatrixTests(unittest.TestCase):
    CASES = (
        (ROOT / "pse" / "sample_with_capabilities.pse", "StoreApi"),
        (ROOT / "tests" / "fixtures" / "webapi_no_infrastructure.pse", "CatalogApi"),
        (ROOT / "tests" / "fixtures" / "clean_architecture.pse", "IdentityApi"),
    )

    def test_supported_generation_matrix_builds(self):
        for source, project_name in self.CASES:
            with self.subTest(source=source.name), tempfile.TemporaryDirectory() as output_dir:
                self.assertTrue(run_pse(str(source), output_dir))
                result = subprocess.run(
                    ["dotnet", "build", os.path.join(output_dir, f"{project_name}.slnx")],
                    cwd=ROOT,
                    text=True,
                    capture_output=True,
                )
                self.assertEqual(result.returncode, 0, result.stdout + result.stderr)


if __name__ == "__main__":
    unittest.main()
