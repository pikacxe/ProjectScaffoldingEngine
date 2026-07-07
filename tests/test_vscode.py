import unittest

from pse.vscode import build_command, default_output_path


class VscodeExtensionTests(unittest.TestCase):
    def test_default_output_is_vsix_under_dist(self):
        self.assertEqual(default_output_path(), "dist/pse-0.1.0.vsix")

    def test_build_command_uses_textx_vscode_generator(self):
        command = build_command("dist/pse.vsix")

        self.assertTrue(command[0].endswith("textx"))
        self.assertIn("generate", command)
        self.assertIn("--target", command)
        self.assertIn("vscode", command)
        self.assertIn("--project-name", command)
        self.assertIn("pse", command)
        self.assertIn("--overwrite", command)


if __name__ == "__main__":
    unittest.main()
