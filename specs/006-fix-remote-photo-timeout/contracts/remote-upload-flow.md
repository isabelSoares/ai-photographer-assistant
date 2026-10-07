# Remote Upload Flow Contract

This contract describes the updated HTTP boundary for the photo-guidance upload flow when accessed remotely. It replaces the synchronous `POST /review` contract from `specs/003-photo-upload-guidance/contracts/upload-flow.md` for the remote deployment path while preserving validation, safety, and result-shape requirements.

## Routes

### `GET /`

- Returns the upload page.
- If the request includes a `job_id` query parameter, the page resumes polling for that job and displays the appropriate status or result.
- The page identifies supported image formats and the maximum upload size.
- The page provides one file selector, a preview or filename, a submit action, and status/result/error regions.

### `POST /review`

- Accepts exactly one multipart photo field named `photo`.
- Rejects an empty field, unsupported format, malformed image, or request exceeding the configured size limit.
- On validation failure, returns `400 Bad Request` with an error state and a plain-language message.
- On success, returns `202 Accepted` immediately with JSON:

  ```json
  {
    "job_id": "uuid-string",
    "state": "queued",
    "queue_position": 1,
    "message": "Your photo is queued for review."
  }
  ```

- The upload is saved to a temporary file and queued for background analysis.
- The response must not expose temporary filesystem paths, model errors, stack traces, or uploaded bytes.

### `GET /status/{job_id}`

- Returns the current state of the analysis job.
- Response shape:

  ```json
  {
    "job_id": "uuid-string",
    "state": "processing",
    "queue_position": null,
    "result": null,
    "error_message": null
  }
  ```

- Valid states: `accepted`, `queued`, `processing`, `completed`, `failed`.
- When `state` is `queued`, `queue_position` is a positive integer indicating the job's place in line.
- When `state` is `completed`, `result` contains the guidance payload defined below.
- When `state` is `failed`, `error_message` contains a safe, user-facing message.
- Returns `404 Not Found` for unknown or expired job IDs.

### Guidance result payload

When `state` is `completed`, `result` has the same shape as the existing upload-flow contract:

```json
{
  "state": "completed",
  "upload_name": "example.jpg",
  "summary": "Human-readable analysis summary",
  "subjects": [],
  "scenes": [],
  "tips": [
    {"text": "Actionable future-session suggestion", "category": "composition", "reason": "Supported analysis signal"}
  ],
  "uncertain": false,
  "notice": null
}
```

## Browser states

- `idle`: no file selected; submit is unavailable.
- `selected`: filename or preview is visible; replacement and submit are available.
- `uploading`: the form is submitting and waiting for the server to accept the upload.
- `queued`: the upload is accepted and waiting for analysis; queue position is visible.
- `processing`: the upload is being analyzed; progress message is visible.
- `completed`: summary, tips, uncertainty notice when applicable, and a new-review action are visible.
- `error`: safe error message plus retry and replacement actions are visible.

## Safety and accessibility requirements

- Escape filenames, summaries, notices, reasons, tip text, and error messages before inserting them into HTML.
- Do not use the original filename as a filesystem path.
- Keep controls keyboard reachable, label the file selector, and provide text alternatives for status changes.
- The layout must remain usable on desktop and mobile-sized screens.
- Do not expose `temporary_path`, model errors, or stack traces in any response.
