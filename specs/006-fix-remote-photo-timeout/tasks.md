---

description: "Executable task list for Fix Remote Photo Upload Timeouts and 502 Errors"

---

# Tasks: Fix Remote Photo Upload Timeouts and 502 Errors

**Input**: Design documents from `/specs/006-fix-remote-photo-timeout/`

**Prerequisites**: `plan.md`, `spec.md`, `research.md`, `data-model.md`, `contracts/remote-upload-flow.md`, and `quickstart.md`

**Organization**: Tasks are grouped by user story so each story can be implemented and tested as an independent increment.

**Testing**: Automated unit and HTTP tests are included because the feature changes the upload request/response contract and the quickstart requires automated validation.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel with other tasks in the same phase when they touch different files and have no incomplete dependency.
- **[Story]**: Maps the task to its user story: `[US1]`, `[US2]`, or `[US3]`.
- Every task names the concrete file or directory it changes or validates.

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Introduce the job-store and worker abstractions without changing the existing batch analyzer or the existing upload validation logic.

- [X] T001 Create `src/upload_jobs.py` with `AnalysisJob`, `ReviewQueue`, and `JobStore` dataclasses matching the fields and state transitions in `specs/006-fix-remote-photo-timeout/data-model.md`.
- [X] T002 [P] Add `MAX_QUEUE_LENGTH` and `JOB_RETENTION_SECONDS` constants to `src/upload_jobs.py` with default values of 10 and 600 respectively.
- [X] T003 [P] Create test module `tests/test_upload_jobs.py` with fixtures for queued, processing, completed, and failed jobs.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Establish the background worker and status contract required by every user story.

**Critical**: Complete this phase before implementing user stories.

- [X] T004 Implement a single background worker thread in `src/upload_jobs.py` that consumes `AnalysisJob`s from `ReviewQueue` one at a time and invokes the existing analysis pipeline.
- [X] T005 [P] Implement job lifecycle transitions (`accepted` → `queued` → `processing` → `completed`/`failed`) in `src/upload_jobs.py`, enforcing immutable terminal states.
- [X] T006 [P] Implement automatic cleanup of temporary files and expired job records in `src/upload_jobs.py` when jobs reach a terminal state or exceed `JOB_RETENTION_SECONDS`.
- [X] T007 Add safe error-result creation in `src/upload_jobs.py` so failed jobs never expose stack traces, model errors, or temporary paths.
- [X] T008 [P] Add service tests in `tests/test_upload_jobs.py` proving one analysis runs at a time, queue ordering is FIFO, and temporary files are removed after success and failure.

**Checkpoint**: Shared job management, single-worker queue, and cleanup behavior are ready; user story work can proceed.

---

## Phase 3: User Story 1 - Upload a Photo Remotely Without Gateway Errors (Priority: P1) 🎯 MVP

**Goal**: A remote user can upload one supported image and receive a fast `202 Accepted` response, then see the result appear automatically without gateway errors.

**Independent Test**: Submit one valid image and verify the response returns within 5 seconds, the page polls status automatically, and the completed result renders correctly. Submit invalid files and verify fast `400` responses with recovery actions.

### Tests for User Story 1

- [X] T009 [P] [US1] Add HTTP tests in `tests/test_upload_server.py` for `POST /review` returning `202 Accepted` with `job_id`, `state`, and `queue_position` for a valid upload.
- [X] T010 [P] [US1] Add HTTP tests in `tests/test_upload_server.py` for `GET /status/{job_id}` returning each valid state (`queued`, `processing`, `completed`, `failed`) with the correct fields.
- [X] T011 [US1] Add service tests in `tests/test_upload_service.py` confirming validation errors (unsupported format, oversized, malformed) still return `400` before a job is created.

### Implementation for User Story 1

- [X] T012 [US1] Update `POST /review` in `src/upload_server.py` to validate the upload, create an `AnalysisJob`, queue it, and return `202 Accepted` with JSON `{job_id, state, queue_position, message}` within 5 seconds.
- [X] T013 [US1] Implement `GET /status/{job_id}` in `src/upload_server.py` returning the current job state as JSON, with `404` for unknown/expired jobs.
- [X] T014 [US1] Update the upload page in `src/upload_server.py` to poll `GET /status/{job_id}` every 2 seconds and render `queued`, `processing`, `completed`, and `error` regions automatically.
- [X] T015 [US1] Preserve the current `job_id` in the page URL after upload so refreshing resumes polling in `src/upload_server.py`.
- [X] T016 [US1] Ensure validation failures in `src/upload_server.py` still render the existing plain-language error page with retry/replacement actions and do not create jobs.

**Checkpoint**: User Story 1 is independently functional: valid remote uploads avoid gateway errors, invalid uploads recover cleanly, and results appear automatically.

---

## Phase 4: User Story 2 - Upload a Second Photo While Another Is Processing (Priority: P1)

**Goal**: A user can submit a second photo while the first is being analyzed; the second upload is queued and both results are matched to the correct filenames.

**Independent Test**: Submit a first photo, immediately submit a second supported photo, and verify both receive `202 Accepted`, the second shows `queue_position: 1`, and each completed result is associated with the correct upload name.

### Tests for User Story 2

- [X] T017 [P] [US2] Add service tests in `tests/test_upload_jobs.py` proving the queue accepts multiple jobs and processes them in FIFO order with only one analysis running at a time.
- [X] T018 [P] [US2] Add HTTP tests in `tests/test_upload_server.py` for two rapid uploads, verifying both return `202 Accepted`, the second has `queue_position: 1`, and results are not mixed up.
- [X] T019 [US2] Add HTTP tests in `tests/test_upload_server.py` for queue overflow, verifying the server returns `503 Service Unavailable` with a plain-language message when the queue is full.

### Implementation for User Story 2

- [X] T020 [US2] Enforce `MAX_QUEUE_LENGTH` in `src/upload_jobs.py` and expose a "server is busy" error when the queue is full.
- [X] T021 [US2] Update `src/upload_server.py` to return `503 Service Unavailable` with a safe message when `ReviewQueue` rejects a new job due to overflow.
- [X] T022 [US2] Display queue position and estimated wait time in the upload page while a job is in `queued` state in `src/upload_server.py`.
- [X] T023 [US2] Ensure completed results in `src/upload_server.py` display the original `upload_name` and are never swapped between jobs.

**Checkpoint**: User Stories 1 and 2 are independently demonstrable as the core remote upload MVP.

---

## Phase 5: User Story 3 - Recover from Slow or Failed Analysis (Priority: P2)

**Goal**: Slow or failed analyses show understandable status, allow retry/replace actions, and do not block future uploads.

**Independent Test**: Force an analysis failure, verify the page shows a safe error with retry/replace actions, then submit a new valid image and verify the old result is replaced and future uploads still work.

### Tests for User Story 3

- [X] T024 [P] [US3] Add service tests in `tests/test_upload_jobs.py` for failed analyses, proving the job ends in `failed` with a safe `error_message` and temporary files are removed.
- [X] T025 [P] [US3] Add HTTP tests in `tests/test_upload_server.py` for `GET /status/{job_id}` returning `failed` state and a safe message after an analysis exception.
- [X] T026 [US3] Add HTTP tests in `tests/test_upload_server.py` proving a failed job does not prevent a subsequent upload from being accepted and queued.

### Implementation for User Story 3

- [X] T027 [US3] Catch analysis exceptions in the worker loop within `src/upload_jobs.py` and convert them to `failed` jobs with safe, user-facing error messages.
- [X] T028 [US3] Render the `error` state in `src/upload_server.py` with retry and replacement controls that clear the current job and allow a new upload.
- [X] T029 [US3] Add a delayed-processing message after 30 seconds of processing in the upload page in `src/upload_server.py`.
- [X] T030 [US3] Ensure a failed or completed job does not hold the queue worker or block new uploads in `src/upload_jobs.py`.

**Checkpoint**: All three user stories are independently testable, with failure recovery and queue behavior covered.

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Validate the complete feature, documentation, security boundaries, and regression safety.

- [X] T031 [P] Update `README.md` with the new remote upload behavior, queue limits, and polling refresh behavior.
- [X] T032 [P] Add regression tests in `tests/test_upload_server.py` confirming `GET /healthz` remains fast and healthy while jobs are queued or processing.
- [X] T033 [P] Add HTML escaping, path-safety, and temporary-file cleanup regression cases to `tests/test_upload_server.py` and `tests/test_upload_jobs.py`.
- [X] T034 Run `.venv/bin/python -m unittest discover -s tests -v` and fix any regressions in `src/upload_server.py`, `src/upload_jobs.py`, or affected tests.
- [X] T035 Run `.venv/bin/python scripts/spec.py all` and verify generated contracts remain consistent with existing specifications.
- [X] T036 Run the manual scenarios in `specs/006-fix-remote-photo-timeout/quickstart.md` against `.venv/bin/python -m src.upload_server` and record any issues.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Phase 1: Setup** has no dependencies and can start immediately.
- **Phase 2: Foundational** depends on Phase 1 and blocks all user stories.
- **Phase 3: User Story 1** depends on Phase 2 and is the recommended MVP increment.
- **Phase 4: User Story 2** depends on the upload and status path from Phase 3; queue-depth behavior builds on the job store from Phase 2.
- **Phase 5: User Story 3** depends on the state and route behavior from Phases 3 and 4.
- **Phase 6: Polish** depends on all desired user stories being complete.

### User Story Dependencies

- **US1 (P1)**: Depends only on the foundational phase. This is the MVP.
- **US2 (P1)**: Depends on US1's fast upload/status boundary; can develop queue tests in parallel with late US1 work.
- **US3 (P2)**: Depends on US1 and US2 state/result behavior.

### Parallel Opportunities

- T002 and T003 can run in parallel after T001.
- T005, T006, and T008 can run in parallel during the foundational phase after T004.
- T009 and T010 can run in parallel before US1 implementation.
- T017 and T018 can run in parallel before US2 implementation.
- T024 and T025 can run in parallel before US3 implementation.
- T031, T032, and T033 can run in parallel after story implementation.

## Parallel Example: User Story 1

```text
Task T009: Add HTTP tests for POST /review returning 202 Accepted with job_id, state, and queue_position
Task T010: Add HTTP tests for GET /status/{job_id} returning each valid state
```

After tests are written, implement T012, T013, T014, T015, and T016 sequentially in `src/upload_server.py`.

## Parallel Example: User Story 2

```text
Task T017: Add service tests proving FIFO queue ordering and single analysis at a time
Task T018: Add HTTP tests for two rapid uploads and non-mixed results
```

After tests are written, implement T020, T021, T022, and T023 in `src/upload_jobs.py` and `src/upload_server.py`.

## Parallel Example: User Story 3

```text
Task T024: Add service tests for failed analyses and cleanup
Task T025: Add HTTP tests for failed job status and safe messages
```

After tests are written, implement T027, T028, T029, and T030.

## Implementation Strategy

### MVP First (User Stories 1 and 2)

1. Complete Phase 1: Setup.
2. Complete Phase 2: Foundational.
3. Complete Phase 3: User Story 1 and verify fast upload acceptance, status polling, and completed results.
4. Complete Phase 4: User Story 2 and verify queue behavior and correct result association.
5. **STOP and VALIDATE** the core remote upload journey with the quickstart scenarios before adding failure-recovery polish.

### Incremental Delivery

1. Deliver the job store and background worker foundation.
2. Add fast upload acceptance and status polling from US1.
3. Add queue visibility and overflow handling from US2.
4. Add failure recovery and delayed-processing messaging from US3.
5. Complete cross-cutting documentation, security, regression, and performance validation.

## Notes

- Every task uses the required `- [ ] T###` checklist format; `[P]` appears only on tasks that can usefully run in parallel; user-story tasks include exactly one `[US#]` label.
- Test tasks precede implementation tasks within each user-story phase.
- The existing batch analyzer (`src/main.py`) and generated contract files remain unchanged unless implementation discovers a concrete compatibility issue.
