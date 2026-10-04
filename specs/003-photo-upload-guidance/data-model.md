# Data Model: Photo Upload Guidance

## Photo Upload

Represents one image selected and submitted for review. It is request-scoped and is not part of the persistent batch history.

| Field | Type | Required | Rules |
|---|---|---:|---|
| original_name | string | yes | Display-only filename; escape before rendering; path components are not used for storage. |
| media_type | string | yes | Determined from decoded content or normalized image output, not trusted solely from the request. |
| byte_size | integer | yes | Must be greater than zero and no more than 10 MiB by default. |
| dimensions | width/height | yes | Must be readable and within the image-processing limits. |
| temporary_path | path | yes during processing | Server-owned temporary location; deleted after review completion or failure. |
| state | enum | yes | `idle`, `selected`, `processing`, `completed`, or `error`. |

## Photo Guidance Result

Represents the completed or failed review associated with one upload.

| Field | Type | Required | Rules |
|---|---|---:|---|
| upload_name | string | yes | Matches the display identity of the submitted upload. |
| summary | string | on completion | Comes from the structured photo analysis and is escaped for display. |
| subjects | list of detections | on completion | Reuses the existing photo-analysis detection shape. |
| scenes | list of detections | on completion | Reuses the existing scene-attribute shape. |
| tips | list of guidance tips | on completion | Must contain at least one supported or clearly general learning tip and no material duplicates. |
| uncertain | boolean | on completion | True when analysis or inferred detections are uncertain. |
| notice | string or null | no | Existing analysis notice, if present. |
| state | enum | yes | `completed` or `error`; never presented as completed when processing failed. |
| error_message | string or null | on error | Plain-language recovery message; must not expose stack traces or filesystem paths. |

## Guidance Tip

Reuses the existing recommendation contract.

| Field | Type | Required | Rules |
|---|---|---:|---|
| text | string | yes | Actionable suggestion framed for future photography. |
| category | string | yes | Existing recommendation category. |
| reason | string | yes | Supported signal or limitation explaining the suggestion. |

## State transitions

```text
idle -> selected       valid photo chosen
idle -> error          selection or validation fails
selected -> processing submit accepted
selected -> selected   replacement photo chosen
processing -> completed analysis succeeds
processing -> error    analysis, timeout, or connection failure
error -> selected      replacement photo chosen
error -> processing    retry accepted with a valid upload
completed -> selected  new photo chosen
completed -> processing new review submitted
```

Invalid transitions include submitting without a selected valid photo, submitting a second review while processing, and displaying a completed result after an error.
