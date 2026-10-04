# Research: Photo Upload Guidance

## Decision: Use a minimal server-rendered web flow

**Rationale**: The repository is a Python 3.13 command-line project with no existing web server, frontend framework, package metadata, or browser entry point. A small Python HTTP entry point with browser-native HTML, CSS, and JavaScript provides the requested upload area without introducing a frontend build system.

**Alternatives considered**:

- A React frontend was rejected because the project has no frontend toolchain and the feature does not require a separate client application.
- Flask or FastAPI was rejected for the first version because it adds a new runtime dependency and application structure before the single-flow requirements justify it.

## Decision: Process one photo synchronously

**Rationale**: The feature specification scopes version 1 to one photo per review. A direct upload-to-result flow is sufficient for the P1 user stories and avoids queues, job identifiers, and persistent sessions.

**Alternatives considered**:

- Background jobs were rejected because they add operational state and recovery complexity for a local or small-scale review flow.
- Batch uploads were rejected because they are explicitly out of scope.

## Decision: Extract a single-image analysis service

**Rationale**: `src/main.run()` is batch-oriented and persists shared result history. The upload flow needs one structured result without writing `results.jsonl` or `cleaned_results.json`. A reusable service should call the existing metadata, detection, analysis, and recommendation functions and return their structured values.

**Alternatives considered**:

- Calling the batch entry point for each upload was rejected because it couples a temporary upload to filename-based history and can leave user images in project output files.

## Decision: Validate content and use temporary storage

**Rationale**: Extension checks alone do not reject malformed or renamed files. Uploaded bytes should be size-checked, decoded as an image, normalized to a model-compatible temporary file where needed, analyzed, and removed in a `finally` path. Use a configurable 10 MiB initial upload limit because the repository currently defines no limit.

**Alternatives considered**:

- Permanent upload storage was rejected because the feature has no gallery requirement and FR-014 limits retention.
- Trusting client-provided MIME types was rejected because they can be falsified.

## Decision: Use explicit review states

**Rationale**: `idle`, `selected`, `processing`, `completed`, and `error` make the UI behavior testable and prevent an old result from being confused with an in-progress or failed review. A new submission replaces the prior result and duplicate submission is disabled while processing.

**Alternatives considered**:

- Inferring state only from whether a result exists was rejected because it cannot distinguish failure, progress, and a stale result.

## Decision: Preserve existing guidance contracts

**Rationale**: `PhotoAnalysisResult` and `PhotographyRecommendations` already encode summaries, detections, uncertainty, reasons, fallback tips, and duplicate prevention. The presentation layer should render these values rather than create a second recommendation format.

**Alternatives considered**:

- Generating new free-form feedback in the upload layer was rejected because it could bypass the signal-aware and cautious wording rules in the existing recommendations module.

## Risks and mitigations

- Blocking model inference can exceed the 30-second user target on slower machines. Show processing state, return a clear timeout/failure message, and measure the end-to-end path during validation.
- Multipart parsing is security-sensitive. Bound request size, validate decoded image content, reject path-like names, escape displayed text, and clean temporary files.
- The existing global model cache may not be safe for concurrent requests. Version 1 should document single-review-at-a-time behavior and prevent overlapping submissions in the UI.
