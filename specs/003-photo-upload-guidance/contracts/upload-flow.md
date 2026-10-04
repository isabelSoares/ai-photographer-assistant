# Upload Flow Contract

This contract describes the user-facing HTTP and browser interaction boundary. It is intentionally implementation-neutral about the HTML rendering library while matching the project's planned server-rendered Python flow.

## Routes

### `GET /`

- Returns the upload page.
- The page identifies supported image formats and the maximum upload size.
- The page provides one file selector, a preview or filename, a submit action, and result/error regions.

### `POST /review`

- Accepts exactly one multipart photo field named `photo`.
- Rejects an empty field, unsupported format, malformed image, or request exceeding the configured size limit.
- On validation failure, returns an error state with a plain-language message and a replacement action.
- On successful processing, returns a completed result containing:

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

- On analysis failure, returns an error state with `state: "error"`, a safe message, and retry/replacement actions. It must not return a misleading partial completed result.
- The response must not expose temporary filesystem paths, model errors, stack traces, or uploaded bytes.

## Browser states

- `idle`: no file selected; submit is unavailable.
- `selected`: filename or preview is visible; replacement and submit are available.
- `processing`: selected upload identity and progress message are visible; duplicate submission is unavailable.
- `completed`: summary, tips, uncertainty notice when applicable, and a new-review action are visible.
- `error`: safe error message plus retry and replacement actions are visible.

## Safety and accessibility requirements

- Escape filenames, summaries, notices, reasons, and tip text before inserting them into HTML.
- Do not use the original filename as a filesystem path.
- Keep controls keyboard reachable, label the file selector, and provide text alternatives for status changes.
- The layout must remain usable on desktop and mobile-sized screens.
