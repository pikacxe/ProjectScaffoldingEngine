import unittest

from textx import GeneratorDesc

from pse.textx_generators import pse_dotnet_generator


class TextxIntegrationTests(unittest.TestCase):
    def test_dotnet_generator_registration_descriptor(self):
        self.assertIsInstance(pse_dotnet_generator, GeneratorDesc)
        self.assertEqual(pse_dotnet_generator.language, "pse")
        self.assertEqual(pse_dotnet_generator.target, "dotnet")


if __name__ == "__main__":
    unittest.main()
