# Implementation Plan: Fix Remote Photo Upload Timeouts and 502 Errors

**Feature directory**: `specs/006-fix-remote-photo-timeout`

**Spec file**: `specs/006-fix-remote-photo-timeout/spec.md`

**Plan file**: `specs/006-fix-remote-photo-timeout/plan.md`

---

## Technical Context

- **Runtime**: Python 3.13, `http.server.ThreadingHTTPServer`, single persistent process.
- **Current request flow**: `POST /review` blocks the HTTP thread while it validates, normalizes, and runs YOLO analysis end-to-end.
- **Current concurrency**: A single `threading.Lock` prevents two analyses from running at once; a second upload receives an immediate 400 error.
- **Deployment model**: The production contract runs `python -m src.upload_server` as a systemd service or Render container, so background threads can live for the process lifetime.
- **Reverse proxy**: A gateway/reverse proxy sits in front of the remote deployment; its exact timeout is unknown.
- **Model loading**: YOLO is loaded lazily and cached globally in `src/yolo.py`; first analysis after startup is especially slow.
- **Open questions / unknowns**:
  - Exact reverse-proxy timeout in production.
  - CPU/memory limits of the remote host.
  - Whether the deployment is Render (container) or VPS (systemd).

## Constitution Check

No `.specify/memory/constitution.md` exists. No governance constraints to evaluate.

## Gate Evaluation

No constitution violations. The plan aligns with the existing deployment contract (single process, ephemeral storage, `/healthz`). Proceed.

---

## Phase 0: Research & Decisions

### Research questions

1. How do we accept uploads quickly while keeping analysis reliable?
2. How do we queue uploads when only one analysis may run at a time?
3. How does the frontend learn about progress and results automatically?

### Decisions and rationale

| Decision | Rationale | Alternatives considered |
|----------|-----------|------------------------|
| Move analysis to a single background worker thread with a FIFO queue | Matches the clarified requirement of exactly one concurrent analysis; fits the existing single-process deployment; no new infrastructure | Celery/RQ: adds Redis/celery dependency; asyncio: requires rewriting request handler |
| Return a job ID immediately from `POST /review` and poll `GET /status/{job_id}` | Guarantees the initial response is fast enough to avoid 502; works with plain `http.server` | WebSockets/SSE: more complex and not needed for 1-second polling |
| Store job state in memory in the server process | Sufficient for v1; ephemeral by design; keeps the deployment contract unchanged | External store (Redis/sqlite): adds persistence and complexity not required |
| Use URL query parameter to preserve job ID across refresh | Users can refresh and still see the status of their upload | localStorage: tied to browser tab; URL is simpler and shareable |
| First poll within 2 seconds, then every 2 seconds while queued/processing | Balances responsiveness and server load | 1-second polling: more responsive but more load; 5-second polling: cheaper but feels slow |

### Open assumptions for implementation

- The reverse proxy timeout is at least 5 seconds, so a quick upload-accepted response avoids 502.
- The remote host can run one YOLO analysis at a time without exhausting memory.
- Results only need to live for the duration of the server process; no cross-restart persistence.

---

## Phase 1: Design & Contracts

### Data model (`data-model.md`)

#### Entity: `AnalysisJob`

Represents one uploaded photo from acceptance through result.

| Field | Type | Description |
|-------|------|-------------|
| `job_id` | `str` | Stable unique identifier returned to the client. |
| `upload_name` | `str` | Original filename for display. |
| `state` | enum | `accepted`, `queued`, `processing`, `completed`, `failed`. |
| `queue_position` | `int \| None` | Position in line when state is `queued`; null otherwise. |
| `result` | `PhotoGuidanceResult \| None` | Completed guidance result when state is `completed`. |
| `error_message` | `str \| None` | Safe message when state is `failed`. |
| `created_at` | `datetime` | When the upload was accepted. |
| `started_at` | `datetime \| None` | When analysis began. |
| `completed_at` | `datetime \| None` | When analysis finished or failed. |

#### Entity: `ReviewQueue`

The ordered collection of pending `AnalysisJob`s waiting for the single analysis worker.

- FIFO ordering.
- Maximum length should be bounded to protect memory; jobs beyond the bound receive a clear “server is busy” response.

#### State transitions

```
accepted → queued → processing → completed
                          ↘ failed
```

### Contracts (`contracts/remote-upload-flow.md`)

#### `POST /review`

- Accepts exactly one multipart photo field named `photo`.
- Validates format, size, and image integrity immediately.
- On success, returns `202 Accepted` with JSON:
  ```json
  {
    "job_id": "uuid-string",
    "state": "queued",
    "queue_position": 1,
    "message": "Your photo is queued for review."
  }
  ```
- On validation failure, returns `400` with a plain-language error.
- The upload is saved to a temporary file and queued for background analysis.

#### `GET /status/{job_id}`

- Returns the current state of the job:
  ```json
  {
    "job_id": "uuid-string",
    "state": "processing",
    "queue_position": null,
    "result": null,
    "error_message": null
  }
  ```
- When `state` is `completed`, `result` contains the guidance payload.
- When `state` is `failed`, `error_message` is a safe, user-facing message.
- Returns `404` for unknown/expired job IDs.

#### `GET /`

- Renders the upload page.
- When a `job_id` query parameter is present, the page resumes polling for that job.
- Provides regions for: idle, selected, uploading, queued, processing, completed, error.

### Quickstart validation guide (`quickstart.md`)

1. **Start the server locally**:
   ```bash
   HOST=127.0.0.1 PORT=8000 .venv/bin/python -m src.upload_server
   ```
2. **Upload a first photo** via the page or curl:
   - Expect a fast `202 Accepted` response with a `job_id`.
   - Expect the page to show “queued” or “processing” status.
3. **Upload a second photo before the first finishes**:
   - Expect another fast `202 Accepted`.
   - Expect to see queue position `1` and an estimated wait message.
4. **Wait for both results**:
   - Expect each result to be matched to the correct filename.
   - Expect no `502 Bad Gateway` errors.
5. **Refresh the page during processing**:
   - Expect the status to resume because the `job_id` is preserved in the URL.
6. **Check `/healthz`**:
   - Expect `200` with the current revision, even while jobs are running.
