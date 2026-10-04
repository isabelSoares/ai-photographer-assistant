# HTTP Deployment Contract

This contract describes the provider-neutral interface required by the production runtime and its release health verification.

## Runtime

- The service starts through the equivalent of `python -m src.upload_server`.
- The production runtime must bind to an externally reachable host, normally `0.0.0.0`.
- The listening port is supplied by the hosting environment through `PORT`, with `8000` as the local default.
- The process is long-running and must not require writable persistent storage for normal upload reviews.
- The tracked `yolo11n.pt` model must be available at runtime.

## Routes

### `GET /`

- Returns the upload interface.
- Returns a successful response when the service is ready to accept review requests.

### `POST /review`

- Accepts one multipart field named `photo`.
- Preserves the existing supported formats and 10 MiB size limit.
- Returns actionable user-facing errors for invalid, unreadable, unsupported, or oversized uploads.
- Does not expose local model paths, stack traces, credentials, or uploaded photo contents in diagnostics.

### `GET /healthz`

- Returns a successful response only when the process can serve requests and its required runtime assets are available.
- Includes the deployed revision identity and a healthy status.
- Returns a non-success response when readiness or required assets are unavailable.
- Must be lightweight and must not run photo inference.

## Release Verification

- The deployment process polls `/healthz` after publication with a bounded timeout and retry interval.
- The reported revision must match the approved immutable artifact identity.
- A mismatch, timeout, or unhealthy response fails the release and prevents it from being reported as complete.
