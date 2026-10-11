# Data Model: Cloudflare Photo Assistant

## Entities

### PhotoUploadRequest

The payload sent from the React component to the Cloudflare Worker.

| Field | Type | Required | Constraints |
|---|---|---|---|
| `image` | string | Yes | Base64 data URL; must start with `data:image/` and be JPEG, PNG, or WEBP. |
| `width` | number | Yes | Pixel width after client resize; must be > 0 and ≤ 1024. |
| `height` | number | Yes | Pixel height after client resize; must be > 0 and ≤ 1024. |
| `filename` | string | Yes | Original filename for display; max 255 characters. |

### DetectedObject

A subject detected by the object-detection model.

| Field | Type | Required | Constraints |
|---|---|---|---|
| `label` | string | Yes | COCO label from DETR, e.g. `person`, `dog`, `car`. |
| `score` | number | Yes | Confidence between 0 and 1. |
| `box` | object | Yes | `{ xmin, ymin, xmax, ymax }` in pixel coordinates. |

### SceneLabel

A scene classification result.

| Field | Type | Required | Constraints |
|---|---|---|---|
| `label` | string | Yes | ImageNet-style label, e.g. `lakeside`, `restaurant`. |
| `score` | number | Yes | Confidence between 0 and 1. |

### GuidanceTip

A photography suggestion returned to the user.

| Field | Type | Required | Constraints |
|---|---|---|---|
| `category` | string | Yes | E.g. `Composition`, `Exposure`, `Subject`. |
| `text` | string | Yes | Plain-language actionable suggestion. |
| `reason` | string | No | Short explanation of why the tip was generated. |

### PhotoGuidanceResult

The complete response from the Worker to the React component.

| Field | Type | Required | Constraints |
|---|---|---|---|
| `summary` | string | Yes | One-sentence description of the photo. |
| `subjects` | DetectedObject[] | Yes | May be empty; sorted by confidence descending. |
| `scenes` | SceneLabel[] | Yes | May be empty; sorted by confidence descending. |
| `tips` | GuidanceTip[] | Yes | Must contain at least one tip, even if generic. |
| `uncertain` | boolean | Yes | True if detections/classifications are weak or missing. |
| `notice` | string | No | Optional notice, e.g. privacy note or fallback explanation. |
| `error_message` | string | No | Set only when analysis fails. |

## Validation rules

- The Worker rejects requests that are not `POST` or that fail CORS preflight.
- The Worker rejects non-image data URLs and data URLs exceeding ~1 MB after decoding.
- The Worker requires `width` and `height` to be positive integers ≤ 1024.
- Detections with `score` < 0.5 are filtered out before tip generation.
- Classification results are limited to the top 3 labels.
- At least one tip must be generated; if no specific rules match, a generic tip is returned.
