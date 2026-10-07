# Data Model: Fix Remote Photo Upload Timeouts and 502 Errors

**Feature**: Fix Remote Photo Upload Timeouts and 502 Errors

## Entity: `AnalysisJob`

Represents one uploaded photo from the moment it is accepted until its guidance result is available or it fails.

| Field | Type | Nullable | Description |
|-------|------|----------|-------------|
| `job_id` | `str` | No | Stable unique identifier returned to the client. Must be URL-safe and non-guessable. |
| `upload_name` | `str` | No | Original filename for display purposes only. Must not be used as a filesystem path. |
| `state` | enum | No | One of `accepted`, `queued`, `processing`, `completed`, `failed`. |
| `queue_position` | `int` | Yes | Position in line when `state` is `queued`; `null` otherwise. Must be a positive integer when present. |
| `result` | `PhotoGuidanceResult` | Yes | Completed guidance result when `state` is `completed`; `null` otherwise. |
| `error_message` | `str` | Yes | Safe, user-facing message when `state` is `failed`; `null` otherwise. |
| `created_at` | `datetime` | No | UTC timestamp when the upload was accepted. |
| `started_at` | `datetime` | Yes | UTC timestamp when analysis began; `null` until `state` becomes `processing`. |
| `completed_at` | `datetime` | Yes | UTC timestamp when analysis finished or failed; `null` until terminal state. |
| `temporary_path` | `Path` | Yes | Filesystem path to the normalized temporary image. Must be deleted when the job reaches a terminal state. |

### State transition rules

```
accepted → queued → processing → completed
                          ↘ failed
```

- A job starts in `accepted` immediately after validation succeeds.
- It moves to `queued` when placed in the review queue.
- It moves to `processing` when the worker begins analysis.
- It ends in `completed` or `failed`.
- Terminal states are immutable.

## Entity: `ReviewQueue`

The ordered collection of pending `AnalysisJob`s waiting for the single analysis worker.

| Property | Rule |
|----------|------|
| Ordering | FIFO based on `created_at`. |
| Max length | Bounded to protect memory; exact limit configurable but default is 10 pending jobs. |
| Overflow behavior | New uploads beyond the limit receive a `503 Service Unavailable` response with a plain-language "server is busy" message. |

## Entity: `JobStore`

In-memory registry of all known jobs.

| Property | Rule |
|----------|------|
| Storage | In-memory dictionary keyed by `job_id`. |
| Retention | Completed and failed jobs are retained for 10 minutes to support page refreshes, then removed. |
| Cleanup | Temporary files associated with removed jobs must be unlinked. |

## Relationships

- `JobStore` contains many `AnalysisJob`s.
- `ReviewQueue` references a subset of `AnalysisJob`s in `accepted` or `queued` states.
- Each `AnalysisJob` produces at most one `PhotoGuidanceResult`.

## Validation rules

- `upload_name` must be escaped before display in HTML.
- `temporary_path` must never be exposed to the client.
- `error_message` must be safe for HTML rendering and must not contain stack traces, model errors, or filesystem paths.
