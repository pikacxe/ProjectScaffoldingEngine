import pathlib
import unittest

from textx import LanguageDesc
from textx.exceptions import TextXSemanticError

from pse.dsl_service import parse_document, validate_document
from pse.language import pse_language


ROOT = pathlib.Path(__file__).resolve().parents[1]


class DslServiceTests(unittest.TestCase):
    def test_valid_sample_has_no_diagnostics(self):
        source = (ROOT / "pse" / "sample.pse").read_text(encoding="utf-8")

        document = parse_document(source, "sample.pse")

        self.assertTrue(document.is_valid)
        self.assertIsNotNone(document.model)
        self.assertEqual(document.diagnostics, ())

    def test_syntax_error_returns_lsp_style_range(self):
        source = "Project Bad target=dotnet { Archetype WebApi Context Orders { Entity Order { Foo } } }"

        diagnostics = validate_document(source, "broken.pse")

        self.assertEqual(len(diagnostics), 1)
        self.assertIn("Expected ID", diagnostics[0].message)
        self.assertEqual(diagnostics[0].range.start.line, 0)
        self.assertGreater(diagnostics[0].range.start.character, 0)
        self.assertEqual(diagnostics[0].to_lsp()["severity"], 1)

    def test_semantic_error_keeps_capability_location(self):
        source = """Project StoreApi target=dotnet {
    Archetype WebApi
    Capabilities {
        Capability UnknownCapability
    }
}"""

        diagnostics = validate_document(source, "capability.pse")

        self.assertEqual(len(diagnostics), 1)
        self.assertIn("Capability 'UnknownCapability' is not recognized", diagnostics[0].message)
        self.assertEqual(diagnostics[0].range.start.line, 3)
        self.assertEqual(diagnostics[0].range.start.character, 8)

    def test_sample_with_capabilities_is_valid(self):
        source = (ROOT / "pse" / "sample_with_capabilities.pse").read_text(encoding="utf-8")

        document = parse_document(source, "sample_with_capabilities.pse")

        self.assertTrue(document.is_valid)
        self.assertEqual(document.diagnostics, ())

    def test_capability_implementation_selection_is_valid(self):
        source = """Project StoreApi target=dotnet {
    Archetype WebApi
    Capabilities {
        Capability CQRS = MediatR
    }
}"""

        document = parse_document(source, "cqrs.pse")

        self.assertTrue(document.is_valid)
        self.assertEqual(document.diagnostics, ())

    def test_unknown_capability_implementation_returns_diagnostic(self):
        source = """Project StoreApi target=dotnet {
    Archetype WebApi
    Capabilities {
        Capability CQRS = Unknown
    }
}"""

        diagnostics = validate_document(source, "cqrs.pse")

        self.assertEqual(len(diagnostics), 1)
        self.assertIn("Capability 'CQRS' implementation 'Unknown' is not recognized", diagnostics[0].message)
        self.assertEqual(diagnostics[0].range.start.line, 3)

    def test_supported_deployment_targets_are_valid(self):
        for target in ("Docker", "DockerSwarm", "Swarm", "Kubernetes", "K8s"):
            source = f"Project StoreApi target=dotnet {{ Archetype WebApi Deployment {target} }}"
            with self.subTest(target=target):
                self.assertTrue(parse_document(source, f"{target}.pse").is_valid)

    def test_unknown_deployment_target_returns_diagnostic(self):
        source = "Project StoreApi target=dotnet { Archetype WebApi Deployment Nomad }"

        diagnostics = validate_document(source, "nomad.pse")

        self.assertEqual(len(diagnostics), 1)
        self.assertIn("Deployment target 'Nomad' is not supported", diagnostics[0].message)

    def test_unimplemented_archetype_returns_diagnostic(self):
        source = "Project Demo target=dotnet { Archetype Microservices }"

        diagnostics = validate_document(source, "microservices.pse")

        self.assertEqual(len(diagnostics), 1)
        self.assertIn("Archetype 'Microservices' is not recognized", diagnostics[0].message)

    def test_duplicate_domain_type_across_contexts_returns_diagnostic(self):
        source = """Project Demo target=dotnet {
    Archetype WebApi
    Context First { Entity User { Guid Id } }
    Context Second { Entity User { Guid Id } }
}"""

        diagnostics = validate_document(source, "duplicates.pse")

        self.assertTrue(any("globally unique" in diagnostic.message for diagnostic in diagnostics))

    def test_duplicate_property_returns_diagnostic(self):
        source = "Project Demo target=dotnet { Archetype WebApi Context C { Entity E { Guid Id String Id } } }"

        diagnostics = validate_document(source, "properties.pse")

        self.assertTrue(any("duplicate entity property" in diagnostic.message for diagnostic in diagnostics))

    def test_empty_entity_returns_diagnostic(self):
        source = "Project Demo target=dotnet { Archetype WebApi Context C { Entity Order {} } }"

        diagnostics = validate_document(source, "empty-entity.pse")

        self.assertEqual(len(diagnostics), 1)
        self.assertIn("must define at least one property", diagnostics[0].message)

    def test_duplicate_capability_returns_diagnostic(self):
        source = """Project Demo target=dotnet {
    Archetype WebApi
    Capabilities {
        Capability logging = serilog
        Capability logging = serilog
    }
}"""

        diagnostics = validate_document(source, "duplicate-capability.pse")

        self.assertEqual(len(diagnostics), 1)
        self.assertIn("declared more than once", diagnostics[0].message)

    def test_unsupported_infrastructure_returns_diagnostic(self):
        source = "Project Demo target=dotnet { Archetype WebApi Infrastructure { Cache Memcached } }"

        diagnostics = validate_document(source, "infrastructure.pse")

        self.assertTrue(any("Memcached" in diagnostic.message for diagnostic in diagnostics))

    def test_property_types_accept_primitives_and_domain_types(self):
        source = """Project StoreApi target=dotnet {
    Archetype WebApi
    Context Identity {
        Entity User {
            Guid Id
            Email Email
        }
        ValueObject Email {
            String Value
        }
    }
}"""

        document = parse_document(source, "types.pse")

        self.assertTrue(document.is_valid)
        user = document.model.contexts[0].entities[0]
        self.assertEqual(user.properties[0].type, "Guid")
        self.assertEqual(user.properties[1].type, "Email")

    def test_textx_language_registration_descriptor(self):
        self.assertIsInstance(pse_language, LanguageDesc)
        self.assertEqual(pse_language.name, "pse")
        self.assertEqual(pse_language.pattern, "*.pse")

    def test_registered_language_runs_pse_semantic_validation(self):
        metamodel = pse_language.metamodel()
        source = """Project StoreApi target=dotnet {
    Archetype WebApi
    Capabilities {
        Capability UnknownCapability
    }
}"""

        with self.assertRaises(TextXSemanticError) as error:
            metamodel.model_from_str(source, file_name="invalid.pse")

        self.assertIn("Capability 'UnknownCapability' is not recognized", str(error.exception))


if __name__ == "__main__":
    unittest.main()
