import os
import tempfile
import unittest

import yaml

from pse.generators.dotnet.deployment import create_deployment
from pse.model.architecture import (
    ArchitectureModel,
    Cache,
    Database,
    Deployment,
    Infrastructure,
    MessageBroker,
    Project,
)
from pse.model.generation_context import GenerationContext
from pse.generators.dotnet.structure_sections import cleanup_inactive_cqrs_files


class DeploymentGeneratorTests(unittest.TestCase):
    def context(self, output_dir, target):
        architecture = ArchitectureModel(
            project=Project(name="StoreApi", archetype="WebApi", target="dotnet"),
            contexts=[],
            infrastructure=Infrastructure(
                database=Database("PostgreSQL"),
                cache=Cache("Redis"),
                broker=MessageBroker("RabbitMQ"),
            ),
            deployment=Deployment(target=target) if target else None,
        )
        return GenerationContext(
            architecture=architecture,
            output_dir=output_dir,
            versions={"dotnet": "10.0", "postgres": "17", "redis": "8", "rabbitmq": "4"},
        )

    def test_missing_deployment_generates_nothing(self):
        with tempfile.TemporaryDirectory() as output_dir:
            create_deployment(self.context(output_dir, None))
            self.assertEqual(os.listdir(output_dir), [])

    def test_inactive_cqrs_files_are_removed_during_regeneration(self):
        with tempfile.TemporaryDirectory() as output_dir:
            cqrs_dir = os.path.join(output_dir, "Cqrs")
            os.makedirs(cqrs_dir)
            requests = os.path.join(cqrs_dir, "OrderRequests.cs")
            messages = os.path.join(cqrs_dir, "OrderMessages.cs")
            open(requests, "w", encoding="utf-8").close()
            open(messages, "w", encoding="utf-8").close()
            context = type("Context", (), {"entities": [type("Entity", (), {"name": "Order"})()]})()

            cleanup_inactive_cqrs_files(output_dir, [context], "wolverine")

            self.assertFalse(os.path.exists(requests))
            self.assertTrue(os.path.exists(messages))

    def test_docker_compose_has_build_healthchecks_and_persistence(self):
        with tempfile.TemporaryDirectory() as output_dir:
            create_deployment(self.context(output_dir, "Docker"))

            with open(os.path.join(output_dir, "docker-compose.yml"), encoding="utf-8") as handle:
                compose = yaml.safe_load(handle)
            dockerfile = self.read(output_dir, "Dockerfile")

            self.assertIn("build", compose["services"]["storeapi"])
            self.assertEqual(
                compose["services"]["storeapi"]["depends_on"]["postgres"]["condition"],
                "service_healthy",
            )
            self.assertIn("postgres-data", compose["volumes"])
            self.assertEqual(compose["services"]["rabbitmq"]["environment"]["RABBITMQ_DEFAULT_USER"], "app")
            self.assertIn("AS build", dockerfile)
            self.assertIn("USER $APP_UID", dockerfile)

    def test_swarm_uses_images_rollouts_overlay_network_and_external_secrets(self):
        with tempfile.TemporaryDirectory() as output_dir:
            create_deployment(self.context(output_dir, "DockerSwarm"))

            stack_path = os.path.join(output_dir, "deploy", "swarm", "stack.yml")
            with open(stack_path, encoding="utf-8") as handle:
                stack = yaml.safe_load(handle)

            app = stack["services"]["storeapi"]
            self.assertNotIn("build", app)
            self.assertEqual(app["deploy"]["update_config"]["order"], "start-first")
            self.assertEqual(stack["networks"]["backend"]["driver"], "overlay")
            self.assertTrue(stack["secrets"]["database-connection"]["external"])
            self.assertTrue(stack["secrets"]["rabbitmq-password"]["external"])
            readme = self.read(output_dir, "deploy/swarm/README.md")
            self.assertIn("docker stack deploy", readme)
            self.assertNotIn("{{AppName}}", readme)

    def test_kubernetes_has_secure_app_and_stateful_dependencies(self):
        with tempfile.TemporaryDirectory() as output_dir:
            create_deployment(self.context(output_dir, "Kubernetes"))

            manifest_path = os.path.join(output_dir, "deploy", "kubernetes", "manifest.yaml")
            with open(manifest_path, encoding="utf-8") as handle:
                documents = list(yaml.safe_load_all(handle))

            by_kind_name = {
                (document["kind"], document["metadata"]["name"]): document
                for document in documents
            }
            app = by_kind_name[("Deployment", "storeapi")]
            container = app["spec"]["template"]["spec"]["containers"][0]

            self.assertEqual(app["spec"]["replicas"], 2)
            self.assertEqual(container["readinessProbe"]["httpGet"]["path"], "/health/ready")
            self.assertTrue(container["securityContext"]["readOnlyRootFilesystem"])
            self.assertIn(("StatefulSet", "postgres"), by_kind_name)
            self.assertIn("volumeClaimTemplates", by_kind_name[("StatefulSet", "postgres")]["spec"])
            postgres = by_kind_name[("StatefulSet", "postgres")]["spec"]["template"]["spec"]["containers"][0]
            self.assertIn(
                {"name": "PGDATA", "value": "/var/lib/postgresql/data/pgdata"},
                postgres["env"],
            )
            self.assertNotIn(("Secret", "storeapi-secrets"), by_kind_name)
            self.assertTrue(os.path.exists(os.path.join(output_dir, "deploy", "kubernetes", "secret.example.yaml")))
            readme = self.read(output_dir, "deploy/kubernetes/README.md")
            self.assertIn("kubectl -n storeapi rollout status", readme)
            self.assertNotIn("{{AppName}}", readme)

    @staticmethod
    def read(output_dir, relative_path):
        with open(os.path.join(output_dir, relative_path), encoding="utf-8") as handle:
            return handle.read()


if __name__ == "__main__":
    unittest.main()
