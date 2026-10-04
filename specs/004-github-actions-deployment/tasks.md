---

description: "Task list for GitHub Actions Deployment"

---

# Tasks: GitHub Actions Deployment

**Input**: Design documents from `/specs/004-github-actions-deployment/`

**Prerequisites**: `plan.md`, `spec.md`, `research.md`, `data-model.md`, `contracts/http-deployment.md`, and `quickstart.md`

**Tests**: Included for the new HTTP health/version contract and workflow configuration because the specification requires independently verifiable validation, release, and recovery behavior.

**Organization**: Tasks are grouped by user story so each release capability can be implemented and validated independently after its stated dependencies.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel with other tasks in the same phase when they touch different files and have no incomplete dependency.
- **[Story]**: Maps the task to its user story: `[US1]`, `[US2]`, or `[US3]`.
- Every task names the concrete file or directory it changes or validates.

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Prepare repository configuration and deployment documentation without changing runtime behavior.

- [x] T001 Review `.gitignore` and add missing Python, workflow artifact, environment, and universal OS patterns without ignoring `yolo11n.pt` in `.gitignore`.
- [x] T002 Create the workflow directory `.github/workflows/` and reserve the three workflow paths `.github/workflows/ci.yml`, `.github/workflows/deploy-production.yml`, and `.github/workflows/rollback-production.yml`.
- [x] T003 [P] Create the deployment operations guide at `docs/deployment.md` covering required production configuration, ownership, release approval, health verification, and rollback inputs.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Establish the runtime contract required by every release workflow.

**Checkpoint**: The application can expose a provider-neutral readiness/version result and the repository has a documented immutable release identity before workflow-specific work begins.

- [x] T004 Add environment-driven host, port, and release revision configuration to `src/upload_server.py`, preserving local defaults of `127.0.0.1` and `8000` while allowing production binding to `0.0.0.0`.
- [x] T005 [P] Add focused runtime configuration and health contract tests in `tests/test_upload_server.py` for local defaults, externally reachable binding configuration, missing model readiness, successful `/healthz`, non-success unhealthy responses, and revision identity.
- [x] T006 Implement `GET /healthz` in `src/upload_server.py` as a lightweight response that verifies required runtime assets, returns healthy status plus the configured revision identity, and never runs photo inference.
- [x] T007 [P] Add deployment contract assertions in `tests/test_deployment_contract.py` for the required runtime command, `PORT` behavior, model inclusion, ephemeral storage assumptions, and `/healthz` response fields.

---

## Phase 3: User Story 1 - Validate Changes Automatically (Priority: P1) 🎯 MVP

**Goal**: Every proposed change and protected-branch update runs the complete repository validation suite and produces one visible release eligibility result.

**Independent Test**: Open a pull request with a passing revision and confirm CI runs tests, specification generation, compilation, and dependency checks; introduce a controlled failure and confirm the required check fails and cannot qualify the revision for release.

### Implementation for User Story 1

- [x] T008 [P] [US1] Define the pull-request and protected-default-branch validation workflow in `.github/workflows/ci.yml` using Python 3.13, explicit dependency installation, minimal permissions, and a unique required check name.
- [x] T009 [US1] Add the required validation commands to `.github/workflows/ci.yml`: `python -m pip check`, `python -m unittest discover -s tests -v`, `python scripts/spec.py all`, and `python -m compileall -q src scripts tests`.
- [x] T010 [US1] Configure `.github/workflows/ci.yml` to report each validation stage, fail on any non-zero or cancelled required check, and avoid exposing environment secrets to pull-request jobs.
- [x] T011 [P] [US1] Add workflow configuration checks in `tests/test_ci_workflow.py` that verify the required triggers, Python version, validation commands, least-privilege permissions, and stable check name in `.github/workflows/ci.yml`.
- [x] T012 [US1] Validate User Story 1 locally with `python -m unittest discover -s tests -v`, `python scripts/spec.py all`, `python -m compileall -q src scripts tests`, and `python -m pip check`, then record the expected CI evidence in `specs/004-github-actions-deployment/quickstart.md`.

**Checkpoint**: User Story 1 is independently functional when proposed changes receive visible pass/fail results and failed required checks cannot proceed to release.

---

## Phase 4: User Story 2 - Publish a Successful Release (Priority: P1)

**Goal**: An explicitly approved, CI-eligible revision is built once, published to the configured production environment, and reported healthy only when the live service serves the same revision.

**Independent Test**: Approve a passing protected-branch revision, run the production workflow, verify the immutable revision identity and `/healthz` result, and confirm that an unapproved or failed revision cannot publish.

**Dependencies**: Requires Phase 2 and completed User Story 1 validation gates.

### Implementation for User Story 2

- [x] T013 [P] [US2] Define the immutable production release workflow in `.github/workflows/deploy-production.yml` with an explicit approved release trigger, `production` environment protection, minimal permissions, and a non-cancelling production concurrency group.
- [x] T014 [US2] Add the build stage to `.github/workflows/deploy-production.yml` so the exact eligible commit produces one SHA-identified artifact containing application files and `yolo11n.pt` while excluding `.env`, user-upload data, `results.jsonl`, and `cleaned_results.json`.
- [x] T015 [US2] Add the publication stage to `.github/workflows/deploy-production.yml` using protected environment configuration and the provider-neutral runtime command from `specs/004-github-actions-deployment/contracts/http-deployment.md`.
- [x] T016 [US2] Add post-publication verification to `.github/workflows/deploy-production.yml` with bounded retries against `/healthz`, requiring a healthy response whose revision matches the approved artifact before reporting success.
- [x] T017 [P] [US2] Add deployment workflow contract checks in `tests/test_deployment_workflows.py` for approval gating, immutable artifact identity, protected environment usage, concurrency, secret isolation, health verification, and failure reporting.
- [x] T018 [US2] Update `docs/deployment.md` with the exact required production environment values, service URL, protected secret names/placeholders, approval ownership, artifact identity, and provider adapter boundary.
- [x] T019 [US2] Validate User Story 2's provider-independent release configuration against the scenarios in `specs/004-github-actions-deployment/quickstart.md`; record live-host prerequisites because no production host or secrets are present in this repository.

**Checkpoint**: User Stories 1 and 2 are independently demonstrable when a passing approved revision can be published and verified without manual reconstruction of release steps.

---

## Phase 5: User Story 3 - Recover Safely from Release Failures (Priority: P2)

**Goal**: Failed or unhealthy releases preserve the prior healthy version where possible, expose safe diagnostics, support retry, and provide a protected rollback workflow.

**Independent Test**: Cause a release or health verification step to fail, confirm the prior version remains available and diagnostics identify the failed stage, then retry the corrected release or roll back to a previously healthy revision.

**Dependencies**: Requires User Story 2's immutable artifact, production environment, health verification, and release status records.

### Implementation for User Story 3

- [x] T020 [P] [US3] Define the protected rollback workflow in `.github/workflows/rollback-production.yml` accepting only a previously successful revision or artifact identity, using the protected `production` environment and serialized production concurrency.
- [x] T021 [US3] Implement rollback publication and post-rollback `/healthz` verification in `.github/workflows/rollback-production.yml`, failing when the requested revision does not match the live health response.
- [x] T022 [US3] Add failure-stage, retry, and rollback diagnostics to `.github/workflows/deploy-production.yml` and `.github/workflows/rollback-production.yml` while masking credentials and excluding uploaded photo contents.
- [x] T023 [P] [US3] Add failure and rollback contract tests in `tests/test_deployment_workflows.py` covering failed publication, prior-version preservation, retry of an eligible revision, overlapping-release prevention, and deliberate rollback to the last healthy revision.
- [x] T024 [US3] Document failure recovery, retry, rollback selection, and incident evidence in `docs/deployment.md` and `specs/004-github-actions-deployment/quickstart.md`.

**Checkpoint**: All user stories are independently testable when a failed release is diagnosable, retryable, and safely reversible without exposing protected data.

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Complete security, documentation, and end-to-end validation across all release paths.

- [x] T025 [P] Audit `.github/workflows/ci.yml`, `.github/workflows/deploy-production.yml`, and `.github/workflows/rollback-production.yml` for least-privilege permissions, immutable third-party action references, secret masking, and pull-request trust boundaries.
- [x] T026 [P] Update `README.md` with CI status expectations, local validation commands, production runtime requirements, and a link to `docs/deployment.md`.
- [x] T027 Run the provider-independent portion of `specs/004-github-actions-deployment/quickstart.md` and capture provider-specific prerequisites still required before production activation.
- [x] T028 Run `python -m unittest discover -s tests -v`, `python scripts/spec.py all`, `python -m compileall -q src scripts tests`, and `python -m pip check`; confirm generated files under `src/generated/` remain synchronized.
- [x] T029 Review the implemented files against `specs/004-github-actions-deployment/spec.md` FR-001 through FR-015 and record any intentionally deferred hosting-provider behavior in `docs/deployment.md`.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Phase 1 Setup**: No dependencies; T001, T002, and T003 can proceed in parallel when they touch separate files.
- **Phase 2 Foundational**: Depends on T002; T004 and T005 must be coordinated because both concern runtime configuration, while T007 can proceed in parallel with T004/T005.
- **Phase 3 User Story 1**: Depends on Phase 2; T008, T009, and T010 share `.github/workflows/ci.yml` and run sequentially, while T011 can proceed in parallel after the workflow shape is agreed.
- **Phase 4 User Story 2**: Depends on User Story 1; T013 through T016 share `.github/workflows/deploy-production.yml` and run sequentially, while T017 and T018 can proceed in parallel once the contract is fixed.
- **Phase 5 User Story 3**: Depends on User Story 2; T020 and T021 share `.github/workflows/rollback-production.yml` and run sequentially, while T023 can proceed in parallel after workflow interfaces are fixed.
- **Phase 6 Polish**: Depends on all desired user stories; T025, T026, and T029 can proceed in parallel before T027/T028 final validation.

### User Story Dependencies

- **User Story 1 (P1)**: Requires Phase 2 runtime contract; no dependency on another user story. This is the MVP.
- **User Story 2 (P1)**: Requires User Story 1's successful CI gate because only validated revisions may be published.
- **User Story 3 (P2)**: Requires User Story 2's artifact, production environment, health verification, and release identity.

### Parallel Opportunities

- T001 and T003 can run in parallel during setup; T002 must complete before foundational work that writes workflow files.
- T005 and T007 can be developed in parallel after the health contract fields are agreed; T006 follows the tests.
- T011 and T018 can be developed in parallel with their respective workflow implementation once workflow interfaces stabilize.
- T020 and T023 can be started in parallel only after the rollback input/output contract is fixed; T021 follows T020.
- T025, T026, and T029 are independent review/documentation tasks and can run in parallel.

## Parallel Example: User Story 1

```text
Task T008: Define workflow triggers and permissions in .github/workflows/ci.yml
Task T011: Write workflow contract checks in tests/test_ci_workflow.py
```

After the workflow shape is agreed, implement T009 and T010 sequentially in `.github/workflows/ci.yml`, then run T012 as the story checkpoint.

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1 setup and Phase 2 health/runtime foundation.
2. Complete Phase 3 CI validation workflow.
3. Run T012 and confirm passing and controlled-failure behavior.
4. Stop with a merge-blocking CI gate before adding production credentials or hosting-provider integration.

### Incremental Delivery

1. Deliver User Story 1 as the merge-blocking validation MVP.
2. Add User Story 2 with a provider adapter, protected production environment, immutable artifact, and health check.
3. Add User Story 3 with safe failure diagnostics, retry, and rollback.
4. Complete cross-cutting security and documentation review before enabling production publication.

## Notes

- `[P]` tasks touch different files or can be prepared without an incomplete dependency; tasks sharing a workflow file remain sequential.
- Tests are required here because the design introduces a new `/healthz` contract and workflow/release acceptance behavior.
- Hosting provider selection is intentionally deferred; the provider-specific adapter must satisfy `contracts/http-deployment.md` before production activation.
