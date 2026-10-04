---

description: "Executable task list for Photo Upload Guidance"
---

# Tasks: Photo Upload Guidance

**Input**: Design documents from `/specs/003-photo-upload-guidance/`

**Prerequisites**: `plan.md`, `spec.md`, `research.md`, `data-model.md`, `contracts/upload-flow.md`, and `quickstart.md`

**Organization**: Tasks are grouped by user story so each story can be implemented and tested as an independent increment.

**Testing**: Automated unit and HTTP tests are included because the feature specification defines acceptance scenarios and the quickstart requires automated validation.

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Establish the new entry points and test locations without changing the existing batch analyzer.

- [X] T001 Create the upload implementation modules `src/upload_service.py` and `src/upload_server.py` and the feature test modules `tests/test_upload_service.py` and `tests/test_upload_server.py` according to the structure in `specs/003-photo-upload-guidance/plan.md`.
- [X] T002 [P] Add a documented local launch command for `src.upload_server` and its default `127.0.0.1:8000` address to `README.md`.
- [X] T003 [P] Add upload-specific constants for supported formats, the default 10 MiB request limit, and the model path in `src/upload_service.py` without changing `src/main.py` batch defaults.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Establish shared safety, result, and state behavior required by every user story.

**Critical**: Complete this phase before implementing user stories.

- [X] T004 Define request-scoped `PhotoUpload`, `PhotoGuidanceResult`, and review-state representations in `src/upload_service.py` using the exact states `idle`, `selected`, `processing`, `completed`, and `error` from `specs/003-photo-upload-guidance/data-model.md`.
- [X] T005 [P] Add shared HTML escaping and safe error-message helpers in `src/upload_server.py` that never expose temporary paths, stack traces, model errors, or uploaded bytes.
- [X] T006 [P] Add test fixtures for valid JPEG bytes, malformed image bytes, oversized payloads, and stubbed analysis results in `tests/test_upload_service.py`.
- [X] T007 Add an upload request/result serialization helper in `src/upload_server.py` matching `specs/003-photo-upload-guidance/contracts/upload-flow.md`, including `state`, `upload_name`, `summary`, `subjects`, `scenes`, `tips`, `uncertain`, and `notice`.

**Checkpoint**: Shared data shapes, safety rules, and test fixtures are ready; user story work can proceed.

---

## Phase 3: User Story 1 - Upload a Photo for Review (Priority: P1) 🎯 MVP

**Goal**: Let a photographer choose one supported image, see it selected, submit it once, and enter a clearly labeled processing state.

**Independent Test**: Select a valid image in the upload page, submit it, and verify the request is accepted for analysis; submit invalid, malformed, and oversized files and verify a plain-language replacement path.

### Tests for User Story 1

- [X] T008 [P] [US1] Add service tests for extension/content validation, empty uploads, malformed images, and the exact 10 MiB maximum in `tests/test_upload_service.py`.
- [X] T009 [P] [US1] Add HTTP tests for `GET /`, multipart field `photo`, filename display, unsupported-file errors, and the `selected` to `processing` transition in `tests/test_upload_server.py`.

### Implementation for User Story 1

- [X] T010 [US1] Implement bounded upload reading, decoded-image validation, supported-format checks, and the exact rule that `byte_size` must be greater than zero and no more than 10 MiB in `src/upload_service.py`.
- [X] T011 [US1] Implement temporary-file creation, image normalization for model-compatible analysis, and guaranteed deletion after success or failure in `src/upload_service.py`.
- [X] T012 [US1] Implement a reusable single-image analysis function in `src/upload_service.py` that calls existing `get_image_info`, `detect_objects`, `build_analysis_result`, and `generate_recommendations` functions without writing `results.jsonl` or `cleaned_results.json`.
- [X] T013 [US1] Implement the upload page, labeled file selector, filename/preview state, submit control, processing status, and `POST /review` multipart handling in `src/upload_server.py`.
- [X] T014 [US1] Disable duplicate submission while processing and reject a second review request while the first review is active in `src/upload_server.py`.

**Checkpoint**: User Story 1 is independently functional: valid files enter analysis, invalid files recover, and no upload is persisted to batch history.

---

## Phase 4: User Story 2 - Receive Actionable Photo Tips (Priority: P1)

**Goal**: Render the existing structured analysis and recommendations as a readable result associated with the submitted photo.

**Independent Test**: Stub a successful analysis response, submit one valid image, and verify the completed page shows the upload identity, summary, at least one distinct actionable tip, supported reasons, and uncertainty wording when applicable.

### Tests for User Story 2

- [X] T015 [P] [US2] Add HTTP tests for a completed response with summary, subjects, scenes, tip text/category/reason, upload identity, and `uncertain` state in `tests/test_upload_server.py`.
- [X] T016 [P] [US2] Add service tests proving existing recommendation fallback behavior is preserved for limited analysis and that material duplicate tips are not rendered twice in `tests/test_upload_service.py`.

### Implementation for User Story 2

- [X] T017 [US2] Map `PhotoAnalysisResult` and `PhotographyRecommendations` into the completed `PhotoGuidanceResult` shape in `src/upload_service.py` without inventing unsupported visual claims.
- [X] T018 [US2] Render the completed summary, detected subjects/scenes, distinct guidance tips, reasons, notices, and uncertainty indicator in `src/upload_server.py`, escaping every user- or model-derived value before HTML insertion.
- [X] T019 [US2] Add responsive, keyboard-reachable upload/result styling and text status alternatives for desktop and mobile-sized screens in `src/upload_server.py`.
- [X] T020 [US2] Add a new-review action that clears the prior result and associates the next completed result with the newly submitted filename in `src/upload_server.py`.

**Checkpoint**: User Stories 1 and 2 are independently demonstrable as the core upload-to-guidance MVP.

---

## Phase 5: User Story 3 - Recover from Analysis Problems (Priority: P2)

**Goal**: Make failed, delayed, interrupted, and replacement reviews safe and recoverable without showing misleading results.

**Independent Test**: Force validation and analysis failures, verify safe error states with retry/replacement actions, then submit a new valid image and verify the old result is replaced.

### Tests for User Story 3

- [X] T021 [P] [US3] Add service tests for analysis exceptions, timeout-like failures, temporary-file cleanup on every failure path, and safe error results in `tests/test_upload_service.py`.
- [X] T022 [P] [US3] Add HTTP tests for retry, replacement, stale-result clearing, interrupted request handling, and rejection of overlapping submissions in `tests/test_upload_server.py`.

### Implementation for User Story 3

- [X] T023 [US3] Implement `error` results with plain-language messages and no partial completed tips when validation or analysis fails in `src/upload_service.py`.
- [X] T024 [US3] Implement retry and replacement controls for the `error` state and ensure the valid transitions in `specs/003-photo-upload-guidance/data-model.md` are enforced in `src/upload_server.py`.
- [X] T025 [US3] Add bounded timeout/connection-failure handling and a visible delayed-processing recovery message in `src/upload_server.py`.
- [X] T026 [US3] Verify all request cleanup paths remove temporary files and do not write uploaded data to `results.jsonl` or `cleaned_results.json` in `src/upload_service.py`.

**Checkpoint**: All three user stories are independently testable, with failure recovery and privacy behavior covered.

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Validate the complete feature, documentation, security boundaries, and regression safety.

- [X] T027 [P] Update `README.md` with supported upload formats, the 10 MiB limit, privacy behavior, and browser validation steps from `specs/003-photo-upload-guidance/quickstart.md`.
- [X] T028 [P] Add HTML escaping, path traversal, request-size, malformed-image, and no-persistent-upload regression cases to `tests/test_upload_server.py` and `tests/test_upload_service.py`.
- [X] T029 Run `.venv/bin/python -m unittest discover -s tests -v` and fix any regressions in `src/upload_service.py`, `src/upload_server.py`, or the affected tests.
- [X] T030 Run `.venv/bin/python scripts/spec.py all` and verify generated contracts remain consistent with the existing specifications.
- [X] T031 Run the manual scenarios in `specs/003-photo-upload-guidance/quickstart.md` against `.venv/bin/python -m src.upload_server` and record any usability or performance issues in `specs/003-photo-upload-guidance/quickstart.md`.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Phase 1: Setup** has no dependencies and can start immediately.
- **Phase 2: Foundational** depends on Phase 1 and blocks all user stories.
- **Phase 3: User Story 1** depends on Phase 2 and is the recommended MVP increment.
- **Phase 4: User Story 2** depends on the upload and analysis path from Phase 3 because its independent test submits a valid photo, although its rendering tests can be prepared in parallel after the shared fixtures exist.
- **Phase 5: User Story 3** depends on the state and route behavior from Phases 3 and 4.
- **Phase 6: Polish** depends on all desired user stories being complete.

### User Story Dependencies

- **US1 (P1)**: Depends only on the foundational phase.
- **US2 (P1)**: Depends on US1's upload/service boundary; can develop rendering tests in parallel with late US1 work.
- **US3 (P2)**: Depends on US1 and US2 state/result behavior.

### Parallel Opportunities

- T002 and T003 can run in parallel after T001.
- T005 and T006 can run in parallel during the foundational phase.
- T008 and T009 can run in parallel before US1 implementation.
- T015 and T016 can run in parallel before US2 implementation.
- T021 and T022 can run in parallel before US3 implementation.
- T027 and T028 can run in parallel after story implementation.
- Different user stories cannot be fully implemented in parallel because US2 consumes US1's upload result and US3 consumes both prior state machines.

## Parallel Example: User Story 1

```text
Task: "Add service tests for extension/content validation, empty uploads, malformed images, and the exact 10 MiB maximum in tests/test_upload_service.py"
Task: "Add HTTP tests for GET /, multipart field photo, filename display, unsupported-file errors, and the selected to processing transition in tests/test_upload_server.py"
```

## Parallel Example: User Story 2

```text
Task: "Add HTTP tests for a completed response with summary, subjects, scenes, tip text/category/reason, upload identity, and uncertain state in tests/test_upload_server.py"
Task: "Add service tests proving existing recommendation fallback behavior is preserved for limited analysis and that material duplicate tips are not rendered twice in tests/test_upload_service.py"
```

## Parallel Example: User Story 3

```text
Task: "Add service tests for analysis exceptions, timeout-like failures, temporary-file cleanup on every failure path, and safe error results in tests/test_upload_service.py"
Task: "Add HTTP tests for retry, replacement, stale-result clearing, interrupted request handling, and rejection of overlapping submissions in tests/test_upload_server.py"
```

## Implementation Strategy

### MVP First (User Stories 1 and 2)

1. Complete Phase 1: Setup.
2. Complete Phase 2: Foundational.
3. Complete Phase 3: User Story 1 and verify valid upload, validation errors, processing state, and cleanup.
4. Complete Phase 4: User Story 2 and verify the readable actionable result.
5. **STOP and VALIDATE** the core upload-to-guidance journey with the quickstart scenarios before adding recovery polish.

### Incremental Delivery

1. Deliver the upload and processing entry point from US1.
2. Add structured guidance rendering from US2 as the core user-facing release.
3. Add retry, replacement, and failure recovery from US3.
4. Complete cross-cutting security, documentation, regression, and performance validation.

## Notes

- Every task uses the required `- [ ] T###` checklist format; `[P]` appears only on tasks that can usefully run in parallel; user-story tasks include exactly one `[US#]` label.
- Test tasks precede implementation tasks within each user-story phase.
- The existing batch analyzer and generated contract files remain unchanged unless implementation discovers a concrete compatibility issue.
