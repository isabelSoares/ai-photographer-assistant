import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CONTRACT = ROOT / "specs/004-github-actions-deployment/contracts/http-deployment.md"
DOCS = ROOT / "docs/deployment.md"


class DeploymentContractTests(unittest.TestCase):
    def test_http_contract_defines_runtime_and_health_requirements(self) -> None:
        contract = CONTRACT.read_text()
        for expected in ("python -m src.upload_server", "0.0.0.0", "PORT", "yolo11n.pt", "GET /healthz", "revision"):
            self.assertIn(expected, contract)

    def test_deployment_documentation_defines_protected_runtime_inputs(self) -> None:
        documentation = DOCS.read_text()
        for expected in ("production", "DEPLOY_HOST", "DEPLOY_USER", "DEPLOY_SSH_KEY", "SERVICE_URL", "APP_REVISION"):
            self.assertIn(expected, documentation)


if __name__ == "__main__":
    unittest.main()
