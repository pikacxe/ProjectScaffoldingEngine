import json
import os
import tempfile
import unittest

from pse.generation_ownership import MANIFEST_NAME, publish_generated_tree
from pse.template_loader import render_template


class GenerationOwnershipTests(unittest.TestCase):
    def test_preserves_modified_files_and_removes_unchanged_stale_files(self):
        with tempfile.TemporaryDirectory() as output_dir, tempfile.TemporaryDirectory() as first_stage:
            self.write(first_stage, "keep.txt", "generated-v1")
            self.write(first_stage, "stale.txt", "generated")
            publish_generated_tree(first_stage, output_dir, overwrite=True)

            self.write(output_dir, "keep.txt", "user change")

            with tempfile.TemporaryDirectory() as second_stage:
                self.write(second_stage, "keep.txt", "generated-v2")
                self.write(second_stage, "new.txt", "new")
                publish_generated_tree(second_stage, output_dir, overwrite=False)

            self.assertEqual(self.read(output_dir, "keep.txt"), "user change")
            self.assertEqual(self.read(output_dir, "new.txt"), "new")
            self.assertFalse(os.path.exists(os.path.join(output_dir, "stale.txt")))

            manifest = json.loads(self.read(output_dir, MANIFEST_NAME))
            self.assertNotIn("keep.txt", manifest["files"])
            self.assertIn("new.txt", manifest["files"])

    def test_overwrite_replaces_modified_owned_file(self):
        with tempfile.TemporaryDirectory() as output_dir, tempfile.TemporaryDirectory() as stage:
            self.write(stage, "owned.txt", "generated")
            self.write(output_dir, "owned.txt", "user change")

            publish_generated_tree(stage, output_dir, overwrite=True)

            self.assertEqual(self.read(output_dir, "owned.txt"), "generated")

    def test_template_loader_rejects_missing_values(self):
        with self.assertRaisesRegex(ValueError, "unresolved placeholders"):
            render_template("dotnet/CSharpClass.cs.tmpl", {"UsingLines": ""})

    @staticmethod
    def write(root, relative_path, content):
        path = os.path.join(root, relative_path)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as handle:
            handle.write(content)

    @staticmethod
    def read(root, relative_path):
        with open(os.path.join(root, relative_path), encoding="utf-8") as handle:
            return handle.read()


if __name__ == "__main__":
    unittest.main()
