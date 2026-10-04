# Quickstart: GitHub Actions Deployment Validation

This guide validates the release design without requiring a specific hosting provider. It covers local CI-equivalent checks and the production workflow contract.

## Prerequisites

- Python 3.13 installed.
- A clean checkout of the repository.
- Dependencies installed from `requirements.txt`.
- The tracked `yolo11n.pt` model present at the repository root for runtime checks.
- For deployment validation, a configured production environment with a service URL and protected credentials.

## Local CI Validation

Run from the repository root:

```bash
python -m pip install -r requirements.txt
python -m pip check
python -m unittest discover -s tests -v
python scripts/spec.py all
python -m compileall -q src scripts tests
```

Expected outcome: each command completes successfully. The specification generator must not leave generated files under `src/generated/` out of sync with the checked-in versions.

## Application Smoke Check

Start the web application using the production-equivalent command and configured externally reachable host/port:

```bash
python -m src.upload_server
```

Verify:

1. `GET /` returns the upload interface successfully.
2. The health endpoint defined by [the HTTP contract](contracts/http-deployment.md) returns a successful response and the running revision identity.
3. `POST /review` accepts one supported photo and returns the existing review experience.
4. Invalid or oversized photos return actionable errors.
5. Temporary upload files are removed after processing.

## Release Validation

1. Open a pull request and confirm all required validation checks run and report a single overall result.
2. Introduce a controlled failing test or validation condition and confirm the change is blocked from release.
3. Merge a passing revision to the protected default branch and confirm the exact merge revision receives validation.
4. Start an approved production release for that revision and confirm the production environment requests approval before exposing credentials.
5. Confirm the deployed service reports the approved revision and passes repeated health checks before the release is marked healthy.
6. Simulate a pre-publication failure and confirm the prior healthy version remains live and diagnostics identify the failed stage.
7. Retry the corrected release without creating an unrelated source change.
8. Run the protected rollback flow for the prior healthy revision and confirm health verification after rollback.

## Evidence to Retain

- Validation check results and test output.
- Commit revision and immutable artifact identity.
- Production approval and deployment status.
- Post-deployment health result and service version.
- Failure diagnostics with secrets and uploaded photos excluded.
- Rollback target and post-rollback health result.
