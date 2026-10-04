# Research: GitHub Actions Deployment

## Decision: Use Python 3.13 with the repository's existing dependency workflow

**Rationale**: The README documents Python 3.13 and `requirements.txt` is the only dependency manifest. CI will create a clean environment, install dependencies, and run `python -m pip check`. Dependency pinning is recommended before production for reproducibility, but is a separate change because the current manifest is intentionally unpinned.

**Alternatives considered**: Poetry or `uv` were rejected because neither is configured in the repository and adding a package-management migration would expand scope.

## Decision: Make the complete repository validation suite the release gate

**Rationale**: The required checks are `python -m unittest discover -s tests -v`, `python scripts/spec.py all`, `python -m compileall -q src scripts tests`, and `python -m pip check`. Together they cover behavior, specification/generated-contract consistency, syntax, and dependency consistency.

**Alternatives considered**: `scripts/verify_results.py` is not a release gate in version 1 because the committed result fixture currently contains duplicates and the command intentionally returns exit code `1` for that valid-but-cleanable condition.

## Decision: Validate pull requests and the protected default branch

**Rationale**: Pull-request validation gives early feedback, while a second run on the protected branch validates the exact merge result eligible for release. A uniquely named required check avoids ambiguous branch-protection rules.

**Alternatives considered**: Running deployment directly from pull requests was rejected because untrusted changes must not receive production credentials or publish to production.

## Decision: Require explicit protected production approval

**Rationale**: Production publication must accept only an eligible commit that passed CI and was deliberately approved. A protected production environment provides reviewer approval and restricts access to deployment secrets.

**Alternatives considered**: Automatic deployment on every push was rejected because the specification requires an approved release event and controlled recovery.

## Decision: Build once and deploy an immutable commit-identified artifact

**Rationale**: The release must identify exactly what was published and make rollback deterministic. The artifact must include the application and tracked `yolo11n.pt` model, while excluding runtime result history and user-upload data.

**Alternatives considered**: Rebuilding from `latest` at deployment time was rejected because it can produce different bits from the validated revision and makes rollback ambiguous.

## Decision: Add a lightweight health/version contract before production deployment

**Rationale**: The current server exposes `/` but no machine-readable health endpoint or deployed-version identity. A dedicated endpoint, preferably `/healthz`, should return a successful status and the running revision identity; deployment will retry health checks before reporting success.

**Alternatives considered**: Checking only process startup was rejected because the process may start while the live route, model, or environment is unusable. Using `/` as the permanent health check is acceptable only as a temporary fallback.

## Decision: Serialize production deployments and provide protected rollback

**Rationale**: The application currently processes one review at a time, and overlapping releases would make the live version unclear. CI may cancel superseded pull-request runs, but an active production deployment must not be cancelled. A rollback workflow will select a previously health-checked commit or release artifact and verify health again.

**Alternatives considered**: Allowing concurrent deployments was rejected because the last completion could overwrite the intended version and complicate incident response.

## Decision: Use protected environment configuration and least-privilege workflow permissions

**Rationale**: Secrets must not be in source, logs, or public artifacts. Production credentials belong only to the protected production environment; cloud OIDC is preferred where the hosting provider supports it. Third-party actions should be pinned to immutable commit SHAs and granted only required permissions.

**Alternatives considered**: Long-lived credentials in repository variables were rejected because they increase exposure and complicate rotation.

## Open Scope Boundary

Hosting provider selection, production URL/domain, TLS termination, autoscaling, dependency lockfile adoption, and multi-environment promotion remain outside this feature. The provider-neutral deployment contract records the inputs the eventual hosting adapter must satisfy.
