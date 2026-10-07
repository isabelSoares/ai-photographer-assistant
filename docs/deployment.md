# Production Deployment

This project uses GitHub Actions for validation and controlled release orchestration. The hosting environment must provide a Linux Python runtime; GitHub Actions does not provide production hosting by itself.

## Runtime Contract

- Start the application with `python -m src.upload_server`.
- Set `HOST=0.0.0.0` and provide the assigned `PORT`.
- Set `APP_REVISION` to the immutable commit SHA being released.
- Make `yolo11n.pt` available at `MODEL_PATH`, or use the repository-root default.
- Expose `GET /healthz` publicly to the configured service URL.
- Use ephemeral local storage for request processing. Do not rely on `results.jsonl`, `cleaned_results.json`, or uploaded photos in production.

## GitHub Configuration

Configure a protected GitHub environment named `production` with required reviewers. Production credentials must be environment secrets and must not be available to pull-request workflows.

The generic SSH deployment adapter expects:

- `DEPLOY_HOST`: Production server hostname.
- `DEPLOY_USER`: SSH user with permission to update the application release directory.
- `DEPLOY_PORT`: SSH port, normally `22`.
- `DEPLOY_SSH_KEY`: Private key for the deployment user.
- `SERVICE_URL`: Public base URL used for health verification.

The target host must already provide Python 3.13, the required system libraries for the packages in `requirements.txt`, an SSH account, and a systemd service named `ai-photographer-assistant.service` that reads `/opt/ai-photographer-assistant/current.env` and starts `/opt/ai-photographer-assistant/current/.venv/bin/python -m src.upload_server`. The deployment workflow installs the immutable release under `/opt/ai-photographer-assistant/releases/<commit-sha>`, writes the non-secret runtime values to `current.env`, and points `/opt/ai-photographer-assistant/current` at that release.

## Release Flow

### Render auto-deploy

For deployments to Render, `.github/workflows/deploy-render.yml` runs automatically
after `.github/workflows/ci.yml` succeeds on `main`:

1. The CI workflow validates the commit.
2. The Render deploy workflow triggers the Render deploy hook.
3. Render builds and deploys the commit.
4. The workflow polls `RENDER_SERVICE_URL/healthz` until the response revision
   matches the deployed commit SHA.

Required GitHub configuration:

- Secret `RENDER_DEPLOY_HOOK_URL` from the Render dashboard.
- Variable `RENDER_SERVICE_URL` pointing to the Render service.

This path does not use the `production` GitHub environment or SSH secrets.

### Manual VPS deployment

1. Pull requests run `.github/workflows/ci.yml`.
2. A passing protected-branch revision can be selected through `workflow_dispatch` in `.github/workflows/deploy-production.yml`.
3. GitHub environment approval is required before deployment secrets are exposed.
4. The workflow builds one SHA-labelled archive, transfers it to the target host, switches the current release, restarts the service, and verifies `SERVICE_URL/healthz` reports the same revision.
5. If health verification fails, the workflow reports the failed stage. The previous `current` symlink remains available for rollback.
6. `.github/workflows/rollback-production.yml` can restore a previously successful release after approval.

## Rollback

Select the previously healthy commit SHA in the rollback workflow. The target release directory must still exist on the production host. The workflow switches `current`, restarts the service, and verifies `/healthz` before reporting success.

## Security Rules

- Never put secrets in source, artifacts, workflow output, or deployment documentation.
- Pull-request jobs must not receive production environment secrets.
- Keep third-party workflow actions pinned to immutable commit SHAs.
- Review deployment logs for accidental model paths, credentials, and uploaded photo content before enabling production publication.
