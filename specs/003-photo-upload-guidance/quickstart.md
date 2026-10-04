# Quickstart: Photo Upload Guidance

## Prerequisites

- Python 3.13 or a compatible Python 3 version.
- Dependencies installed from `requirements.txt`.
- The existing `yolo11n.pt` model file at the repository root.
- A supported test image such as `photos/test.jpg`.

## Planned local run

From the repository root:

```bash
.venv/bin/python -m src.upload_server
```

Open `http://127.0.0.1:8000/` in a browser.

## Manual validation

1. Confirm the page identifies the supported formats and upload limit.
2. Select `photos/test.jpg`; verify its filename or preview appears and submit becomes available.
3. Submit the image; verify a processing state appears and duplicate submission is disabled.
4. Verify the completed page associates the result with the selected filename and shows a summary plus at least one actionable tip.
5. Repeat with an unsupported extension, a non-image file, and an oversized file; verify a plain-language error and replacement path.
6. Force an analysis failure; verify no completed tips are shown and retry/replacement actions remain available.
7. Start a new review; verify the previous result is replaced and the new result is associated with the new photo.
8. Inspect the temporary directory after completion and failure; verify the uploaded temporary file is removed.

## Automated validation

Run the existing suite:

```bash
.venv/bin/python -m unittest discover -s tests -v
```

Run spec and contract validation:

```bash
.venv/bin/python scripts/spec.py all
```

The feature tests should cover the service and HTTP boundary described in [upload-flow.md](contracts/upload-flow.md), including validation, state transitions, safe errors, result shape, duplicate prevention, and temporary-file cleanup.
