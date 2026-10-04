# Implementation Plan: Photo Upload Guidance

**Branch**: `003-photo-upload-guidance` | **Date**: 2026-10-04 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `/specs/003-photo-upload-guidance/spec.md`

**Note**: This template is filled in by the `/speckit.plan` command; its definition describes the execution workflow.

## Summary

Add a one-photo browser upload flow that validates image content, performs the existing analysis and recommendation pipeline for a temporary file, and renders a safe, actionable guidance result. Use a small server-rendered Python entry point rather than adding a frontend framework or persistent upload history. Keep the existing batch CLI and generated analysis contracts intact.

## Technical Context

<!--
  ACTION REQUIRED: Replace the content in this section with the technical details
  for the project. The structure here is presented in advisory capacity to guide
  the iteration process.
-->

**Language/Version**: Python 3.13 or compatible Python 3

**Primary Dependencies**: Existing Pillow, pillow-heif, ultralytics, OpenCV, and NumPy dependencies; Python standard-library HTTP and multipart handling for the new entry point

**Storage**: Request-scoped temporary files only; no upload persistence or batch-history writes

**Testing**: Standard-library `unittest`, temporary directories, mocked analysis boundaries, and HTTP-level tests

**Target Platform**: Local Python process serving desktop and mobile-sized web browsers

**Project Type**: Existing Python CLI extended with a small local web service and reusable single-image analysis service

**Performance Goals**: 90% of valid submissions show a completed result or clear recovery message within 30 seconds under normal service conditions; UI feedback appears immediately when processing starts

**Constraints**: One upload per review; 10 MiB default request limit; validate decoded image content; reject malformed or unsupported files; escape rendered text; prevent overlapping submissions; delete temporary files after processing; do not expose paths, stack traces, or image bytes

**Scale/Scope**: Version 1 local/small-scale single-photo reviews; one upload page, one review route, five explicit UI states; batch uploads, galleries, accounts, and background job infrastructure are out of scope

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

The constitution file contains only unfilled template placeholders and therefore defines no enforceable project principles or gates. No violation is identified. The plan nevertheless preserves the existing generated-contract workflow, standard-library test conventions, cautious recommendation rules, and minimal scope.

**Gate status**: PASS. No unresolved constitutional requirement is present.

## Project Structure

### Documentation (this feature)

```text
specs/003-photo-upload-guidance/
├── plan.md              # This file (/speckit.plan command output)
├── research.md          # Phase 0 output (/speckit.plan command)
├── data-model.md        # Phase 1 output (/speckit.plan command)
├── quickstart.md        # Phase 1 output (/speckit.plan command)
├── contracts/           # Phase 1 output (/speckit.plan command)
└── tasks.md             # Phase 2 output (/speckit.tasks command - NOT created by /speckit.plan)
```

### Source Code (repository root)
<!--
  ACTION REQUIRED: Replace the placeholder tree below with the concrete layout
  for this feature. Delete unused options and expand the chosen structure with
  real paths (e.g., apps/admin, packages/something). The delivered plan must
  not include Option labels.
-->

```text
src/
├── main.py                         # Existing batch analysis entry point
├── upload_service.py               # Single-upload validation and analysis orchestration
├── upload_server.py                # Server-rendered upload/review boundary
├── image_analysis.py               # Existing metadata extraction
├── photo_analysis.py               # Existing structured analysis
└── recommendations.py              # Existing guidance generation

tests/
├── test_upload_service.py           # Validation, cleanup, and orchestration tests
├── test_upload_server.py             # HTTP and browser-state tests
└── existing test modules
```

**Structure Decision**: Keep the existing single-project `src/` and `tests/` layout. Add the upload service beside the existing analysis modules and add a server entry point without creating a frontend project or changing generated contracts. Feature documentation remains under `specs/003-photo-upload-guidance/`.

## Complexity Tracking

No constitutional violations or complexity exceptions require tracking.

## Phase 0: Research

Research is complete in [research.md](research.md). Decisions cover delivery approach, single-image orchestration, temporary storage, validation, explicit state handling, existing contracts, and risks.

## Phase 1: Design

- [data-model.md](data-model.md) defines request-scoped upload data, guidance results, tips, and state transitions.
- [contracts/upload-flow.md](contracts/upload-flow.md) defines the browser-facing routes, result shape, states, and safety requirements.
- [quickstart.md](quickstart.md) defines manual and automated validation scenarios.

## Post-Design Constitution Check

**Status**: PASS. The design remains within the existing single Python project, uses the existing structured analysis and recommendation contracts, avoids persistent photo storage, and introduces no conflict with the constitution's unfilled template. No complexity exception is needed.
