# Research: Fix Remote Photo Upload Timeouts and 502 Errors

**Feature**: Fix Remote Photo Upload Timeouts and 502 Errors
**Date**: 2026-10-07

## Research Questions

1. How do we accept uploads quickly while keeping analysis reliable?
2. How do we queue uploads when only one analysis may run at a time?
3. How does the frontend learn about progress and results automatically?

## Findings

### Current behavior

- `src/upload_server.py` runs analysis synchronously inside the `POST /review` request handler.
- A `threading.Lock` (`review_lock`) ensures only one analysis runs at a time; a second concurrent upload gets an immediate 400 error.
- The YOLO model is loaded lazily on first inference, making the first analysis after startup particularly slow.
- When the site is exposed through a reverse proxy, long-running requests exceed the proxy timeout and produce a `502 Bad Gateway`.

### Decision 1: Background worker with FIFO queue

**Decision**: Move photo analysis out of the request handler into a single background worker thread that consumes from a FIFO queue.

**Rationale**:
- Satisfies the clarified requirement of exactly one concurrent analysis.
- Fits the existing single-process deployment (`python -m src.upload_server`) without adding infrastructure.
- Avoids holding HTTP connections open during analysis, eliminating the 502 timeout cause.
- Simpler than introducing Celery, RQ, or an async framework for a single-worker queue.

**Alternatives considered**:
- **Celery/RQ**: Requires a broker and extra operational complexity; overkill for one worker.
- **asyncio**: Would require rewriting the request handler and compatibility with blocking YOLO inference.
- **Process pool**: Adds serialization overhead and does not match the single-analysis requirement.

### Decision 2: Job ID + status polling

**Decision**: `POST /review` returns a `202 Accepted` response with a job ID; the frontend polls `GET /status/{job_id}`.

**Rationale**:
- Guarantees the upload response is fast enough to avoid gateway timeouts.
- Works with the standard library `http.server` without WebSocket or SSE support.
- Polling is simple, robust, and easy to test.

**Alternatives considered**:
- **Server-Sent Events (SSE)**: Cleaner for live updates but not supported by the current server architecture.
- **WebSockets**: Overkill for a single-page status update and not supported by `http.server`.
- **Long polling**: Reintroduces the timeout risk we are trying to avoid.

### Decision 3: In-memory job store

**Decision**: Keep job state in memory inside the server process, with a bounded queue and a 10-minute retention window for completed/failed jobs.

**Rationale**:
- Sufficient for the request-scoped review flow.
- Keeps the existing privacy/retention contract (no persistent user gallery).
- Avoids adding a database or external cache.

**Alternatives considered**:
- **SQLite on disk**: Adds persistence and file-management concerns not required by the spec.
- **Redis**: Adds infrastructure dependency.

### Decision 4: Preserve job ID in URL for refresh recovery

**Decision**: After a successful upload, update the page URL to include `?job_id=...` so refreshing resumes polling.

**Rationale**:
- Simple and reliable.
- Does not depend on browser storage.
- Matches the auto-update-on-same-page requirement.

**Alternatives considered**:
- **localStorage/sessionStorage**: More fragile across tabs and incognito modes.
- **Cookie-based session**: Adds stateful session management and privacy concerns.

## Assumptions Carried into Design

- The reverse proxy timeout is at least 5 seconds.
- The remote server can run one YOLO analysis at a time within available memory.
- Completed/failed job results need only persist for ~10 minutes to support page refreshes.
- The deployment remains a single persistent process, so background threads survive across requests.
