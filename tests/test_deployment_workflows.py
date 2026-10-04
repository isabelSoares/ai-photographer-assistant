import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DEPLOY = ROOT / ".github/workflows/deploy-production.yml"
ROLLBACK = ROOT / ".github/workflows/rollback-production.yml"


class DeploymentWorkflowTests(unittest.TestCase):
    def test_production_deployment_is_approved_immutable_and_health_checked(self) -> None:
        workflow = DEPLOY.read_text()
        for expected in (
            "workflow_dispatch:",
            "revision:",
            "environment:",
            "name: production",
            "group: production",
            "cancel-in-progress: false",
            "CI / validate",
            "yolo11n.pt",
            "results.jsonl",
            "cleaned_results.json",
            "DEPLOY_SSH_KEY",
            "SERVICE_URL",
            "current.env",
            "APP_REVISION",
            "/healthz",
            "payload.get(\"revision\")",
        ):
            self.assertIn(expected, workflow)

    def test_rollback_requires_an_existing_release_and_health_verification(self) -> None:
        workflow = ROLLBACK.read_text()
        for expected in (
            "workflow_dispatch:",
            "Previously healthy commit SHA to restore",
            "name: production",
            "cancel-in-progress: false",
            'test -d "$base/releases/$REVISION"',
            "ln -sfn",
            "/healthz",
            "DEPLOY_SSH_KEY",
        ):
            self.assertIn(expected, workflow)

    def test_workflows_pin_third_party_actions(self) -> None:
        for path in (DEPLOY, ROOT / ".github/workflows/ci.yml"):
            for line in path.read_text().splitlines():
                if "uses: actions/" in line:
                    self.assertRegex(line, r"uses: actions/[\w-]+@[0-9a-f]{40}")


if __name__ == "__main__":
    unittest.main()
