# Contract: Photo Assistant API

## Endpoint

```text
POST https://<your-worker>.workers.dev/
```

## CORS

- Allowed methods: `OPTIONS`, `POST`.
- Allowed origin: configured portfolio origin (e.g. `https://isabelsoares.github.io`).
- Allowed headers: `Content-Type`.

## Request

```json
{
  "image": "data:image/jpeg;base64,/9j/4AAQ...",
  "width": 1024,
  "height": 768,
  "filename": "photo.jpg"
}
```

### Field rules

- `image`: must be a base64 data URL starting with `data:image/` (jpeg, png, or webp).
- `width` and `height`: integers, each > 0 and ≤ 1024.
- `filename`: string, max 255 characters.

## Response (success)

Status: `200 OK`

```json
{
  "summary": "A person standing in front of a bright sky.",
  "subjects": [
    {
      "label": "person",
      "score": 0.97,
      "box": { "xmin": 100, "ymin": 50, "xmax": 400, "ymax": 600 }
    }
  ],
  "scenes": [
    { "label": "sky", "score": 0.91 }
  ],
  "tips": [
    {
      "category": "Exposure",
      "text": "The background sky is brighter than the subject. Try exposing for the person or use fill flash.",
      "reason": "Detected person is darker than the overall scene."
    }
  ],
  "uncertain": false,
  "notice": null,
  "error_message": null
}
```

## Response (client error)

Status: `400 Bad Request`

```json
{
  "error": "Invalid image format. Please upload a JPG, PNG, or WEBP photo."
}
```

## Response (server error)

Status: `500 Internal Server Error`

```json
{
  "error": "The photo could not be analyzed. Please try again or choose another photo."
}
```

## Error cases

- Unsupported or missing image.
- Image dimensions out of allowed range.
- Missing required fields.
- Workers AI model failure or quota exceeded.
- Worker runtime exception.
