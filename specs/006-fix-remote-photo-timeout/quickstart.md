# Quickstart: Fix Remote Photo Upload Timeouts and 502 Errors

**Feature**: Fix Remote Photo Upload Timeouts and 502 Errors

This guide provides runnable validation scenarios for the remote upload reliability improvements.

## Prerequisites

- Python 3.13 or compatible.
- Project virtual environment installed and activated.
- YOLO model file available at the project root (`yolo11n.pt`) or at `MODEL_PATH`.

## Start the server locally

```bash
HOST=127.0.0.1 PORT=8000 .venv/bin/python -m src.upload_server
```

Open `http://127.0.0.1:8000/` in a browser.

## Scenario 1: First upload returns quickly

1. Select one supported photo (JPG, PNG, WEBP, BMP, TIFF, or HEIC, up to 10 MiB).
2. Submit the form.
3. **Expected**: The page updates to a `queued` or `processing` state within 5 seconds and the URL contains a `job_id` parameter.
4. Wait for analysis to complete.
5. **Expected**: The completed guidance result appears without a page reload and without a `502 Bad Gateway` error.

## Scenario 2: Second upload while first is processing

1. Upload a first photo and wait until the state shows `processing`.
2. Without waiting for the first result, upload a second supported photo.
3. **Expected**: The second upload is accepted immediately with a `queued` state and a `queue_position` of `1`.
4. Wait for both analyses to complete.
5. **Expected**: Each result is matched to the correct filename.

## Scenario 3: Refresh during processing

1. Upload a photo and note the `job_id` in the URL.
2. Refresh the browser before analysis completes.
3. **Expected**: The page resumes polling the same job and continues to show the current status.

## Scenario 4: Validation errors still recover cleanly

1. Try to upload an unsupported file, an oversized file, or a corrupted image.
2. **Expected**: The page shows a plain-language error within 5 seconds and offers retry/replacement actions.
3. Select a valid photo and submit.
4. **Expected**: The valid upload proceeds normally.

## Scenario 5: Health endpoint remains healthy under load

1. While one or more uploads are queued or processing, request `GET /healthz`.
2. **Expected**: The response is `200 OK` with the current revision; it does not run photo inference.

## Automated validation

Run the existing test suite and spec checks:

```bash
.venv/bin/python -m unittest discover -s tests -v
.venv/bin/python scripts/spec.py all
.venv/bin/python -m compileall -q src scripts tests
```

All tests should pass without regressions in batch analysis or the existing upload validation behavior.
