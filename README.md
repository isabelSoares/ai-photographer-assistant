# AI Photographer Assistant

An experimental Python assistant that analyzes photographs with YOLO and produces
structured observations and photography recommendations.

## Current Capabilities

- Analyze JPEG and other converted image files with YOLO
- Report detected subjects, scene attributes, confidence, and uncertainty
- Generate rule-based composition, lighting, and framing suggestions
- Process every supported image in `converted_photos/`
- Store one JSON Lines result per processed image in `results.jsonl`
- Validate and clean duplicate result history

The assistant does not edit images or draw detection boxes. Its output is text and structured JSON intended to support future conversational feedback.

## Requirements

- Python 3.13 or compatible Python 3 version
- A YOLO model file at the project root, currently `yolo11n.pt`
- Runtime packages used by the source code: `ultralytics`, `Pillow`,
  `pillow-heif`, `opencv-python`, and `numpy`

The repository includes a local `.venv` in the current development environment.
For a new environment:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Run Analysis

Place supported images in `converted_photos/`, then run from the project root:

```bash
.venv/bin/python src/main.py
```

The program processes `.jpg`, `.jpeg`, `.png`, `.webp`, `.bmp`, and `.tiff` files.
It appends one UTF-8 JSON object per line to `results.jsonl`. Running the batch again can create duplicate records for the same filename.

## Verify History

Validate the result history and create a cleaned copy:

```bash
.venv/bin/python scripts/verify_results.py
```

The verifier reads one JSON object per line from `results.jsonl` without modifying it. It keeps the first record for each filename and writes `cleaned_results.json` as one UTF-8 JSON document with this shape:

```json
{
    "statistics": {
        "total_records": 3,
        "duplicates_removed": 1,
        "unique_records": 2
    },
    "records": []
}
```

Exit codes are part of the command contract:

- `0`: valid results with no duplicates
- `1`: valid results with duplicates; cleaned output was created
- `2`: missing, invalid, or structurally invalid input

The verifier accepts an optional results path:

```bash
.venv/bin/python scripts/verify_results.py path/to/results.jsonl
```

## Test

Run the acceptance tests:

```bash
.venv/bin/python -m unittest discover -s tests -v
```

Run Python compilation and spec validation:

```bash
.venv/bin/python scripts/spec.py all
.venv/bin/python -m py_compile src/main.py src/photo_analysis.py src/recommendations.py
```

## Spec-Driven Workflow

The `specs/` directory defines behavior. Each feature spec contains human-readable requirements and, where code needs a stable shape, a fenced JSON `Data contract`.
The generator validates these contracts and creates Python dataclasses:

```text
Markdown specification
    -> spec check
    -> generated Python contracts
    -> implementation
    -> acceptance tests
```

Run the complete spec workflow after changing a contract:

```bash
.venv/bin/python scripts/spec.py all
```

Generated files under `src/generated/` must not be edited manually. The command-line verifier is implemented manually because the current generator creates data models,not complete programs.

## Project Structure

```text
src/main.py                         Batch analysis entry point
src/yolo.py                         YOLO inference
src/image_analysis.py               Image metadata extraction
src/photo_analysis.py               Structured detection results
src/recommendations.py              Rule-based photography advice
src/generated/                      Generated dataclass contracts
scripts/spec.py                     Spec checker and contract generator
scripts/verify_results.py           Duplicate-history verifier
specs/                              Product and behavior specifications
docs/decisions/                     Technical decision records
tests/                              Acceptance tests
```

## Documentation Map

- `README.md`: how to install, run, test, and operate the project
- `specs/`: what the product must do
- `docs/decisions/`: why important technical choices were made
