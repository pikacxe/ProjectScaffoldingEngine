import importlib.util
import json
import os
import tempfile
import unittest
import zipfile

from pse.vscode import build_command, default_output_path, generate_vscode_extension


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

    @unittest.skipUnless(
        importlib.util.find_spec("textx_gen_vscode"),
        "textx-gen-vscode is not installed",
    )
    def test_generated_vsix_contributes_pse_language_and_syntax(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            output_path = os.path.join(temp_dir, "pse-test.vsix")

            result = generate_vscode_extension(output_path)

            self.assertEqual(result, 0)
            with zipfile.ZipFile(output_path) as archive:
                package_json = json.loads(
                    archive.read("extension/package.json").decode("utf-8")
                )
                syntax_json = archive.read("extension/syntaxes/pse.json").decode(
                    "utf-8"
                )
                extension_js = archive.read("extension/extension.js").decode("utf-8")

            language = package_json["contributes"]["languages"][0]
            self.assertEqual(language["id"], "pse")
            self.assertIn(".pse", language["extensions"])
            self.assertIn("*.pse", language["filenamePatterns"])
            self.assertIn("PSE", language["aliases"])
            self.assertIn("textX.textX", package_json["extensionDependencies"])
            self.assertIn("Project", syntax_json)
            self.assertIn("Context", syntax_json)
            self.assertIn("Entity", syntax_json)
            self.assertIn("Guid", syntax_json)
            self.assertIn("String", syntax_json)
            self.assertIn("Int", syntax_json)
            self.assertIn("registerCompletionItemProvider", extension_js)
            self.assertIn("PRIMITIVE_TYPES", extension_js)
            self.assertIn("Guid", extension_js)
            self.assertIn("DockerSwarm", extension_js)
            self.assertIn("Kubernetes", extension_js)
            self.assertIn("Project", extension_js)
            self.assertIn("registerDocumentFormattingEditProvider", extension_js)
            self.assertIn("formatPseText", extension_js)
            self.assertNotIn("{{Keywords}}", extension_js)
            self.assertNotIn("{{PrimitiveTypes}}", extension_js)
            self.assertNotIn("{{Values}}", extension_js)


if __name__ == "__main__":
    unittest.main()
