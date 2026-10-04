import unittest
from pathlib import Path


WORKFLOW = Path(__file__).resolve().parents[1] / ".github/workflows/ci.yml"


class CIWorkflowTests(unittest.TestCase):
    def test_ci_workflow_has_required_triggers_and_checks(self) -> None:
        workflow = WORKFLOW.read_text()
        for expected in (
            "pull_request:",
            "push:",
            "branches: [main]",
            'python-version: "3.13"',
            "python -m pip check",
            "python -m unittest discover -s tests -v",
            "python scripts/spec.py all",
            "python -m compileall -q src scripts tests",
            "name: CI / validate",
            "contents: read",
        ):
            self.assertIn(expected, workflow)

    def test_ci_workflow_has_no_production_environment_or_secrets(self) -> None:
        workflow = WORKFLOW.read_text()
        self.assertNotIn("environment:", workflow)
        self.assertNotIn("secrets.", workflow)


if __name__ == "__main__":
    unittest.main()
