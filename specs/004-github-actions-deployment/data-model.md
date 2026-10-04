# Data Model: GitHub Actions Deployment

## Proposed Change

Represents one source revision entering validation.

### Fields

- `revision`: Immutable commit identifier.
- `source_context`: Pull request or protected-branch context.
- `checks`: Required validation checks and their outcomes.
- `eligibility`: `pending`, `eligible`, `blocked`, or `cancelled`.
- `diagnostics`: Links or references to retained check output, excluding secrets.

### Validation Rules

- `revision` is required and must identify the exact source under test.
- Every required check must finish successfully before `eligibility` becomes `eligible`.
- A failed, cancelled, or inconclusive required check makes the revision `blocked` or `cancelled`.

## Release

Represents one approved attempt to publish an eligible revision.

### Fields

- `revision`: The eligible source revision being published.
- `artifact_id`: Immutable build artifact associated with the revision.
- `approval`: Approval state and approving maintainer reference.
- `status`: `pending`, `running`, `healthy`, `failed`, or `rolled_back`.
- `environment`: The target production environment.
- `started_at` and `completed_at`: Release timing metadata.
- `failure_stage`: Stage that failed, when applicable.
- `diagnostics`: Safe references to release output.

### State Transitions

```text
pending -> running -> healthy
pending -> failed
running -> failed
healthy -> rolled_back
```

Only an eligible revision with explicit approval may enter `running`. A failed release may be retried after correction. A rollback is a new protected release of a previously healthy revision.

## Live Version

Represents the revision currently serving users.

### Fields

- `revision`: Commit identity of the serving release.
- `artifact_id`: Artifact identity used for publication.
- `health`: `unknown`, `healthy`, or `unhealthy`.
- `published_at`: Time the version became live.
- `service_url`: Configured public URL, if available.

### Validation Rules

- A release is not considered complete until the live version is `healthy`.
- The health response must expose enough version identity to compare the live revision with the approved release.
- The previous healthy version remains the rollback target until a newer version is verified healthy.

## Release Configuration

Represents protected deployment inputs rather than user data.

### Fields

- `environment_name`: Production environment identifier.
- `service_url`: URL used for post-deployment verification.
- `credentials`: Protected deployment credentials or OIDC configuration.
- `runtime_settings`: Non-secret host, port, timeout, and model settings.
- `reviewers`: Maintainers authorized to approve production deployment.

### Validation Rules

- Credentials are available only to approved production jobs.
- Secrets must not be written to source, artifacts, or logs.
- Required configuration must be validated before publication begins.
