# Implementation Plan: GitHub Actions Deployment

**Branch**: `004-github-actions-deployment` | **Date**: 2026-10-04 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `/specs/004-github-actions-deployment/spec.md`

## Summary

Add a protected GitHub Actions release path for the Python photo-review web application. Pull requests and protected-branch updates will run the repository's complete validation suite, while production publication will require a validated source revision, explicit approval, protected configuration, serialized deployment, post-release health verification, and a documented rollback path. The implementation will remain hosting-provider neutral and package the tracked YOLO model with the exact commit-specific release artifact.

## Technical Context

<!--
  ACTION REQUIRED: Replace the content in this section with the technical details
  for the project. The structure here is presented in advisory capacity to guide
  the iteration process.
-->

**Language/Version**: Python 3.13 (repository documents Python 3.13 or compatible Python 3)

**Primary Dependencies**: `ultralytics`, `Pillow`, `pillow-heif`, `opencv-python`, `numpy`; GitHub Actions workflow actions

**Storage**: Ephemeral local filesystem for web request processing; `yolo11n.pt` packaged with the release; result history excluded from live request handling

**Testing**: `python -m unittest discover -s tests -v`; `python scripts/spec.py all`; `python -m compileall -q src scripts tests`; `python -m pip check`

**Target Platform**: GitHub-hosted Linux CI runner and one provider-neutral Linux/Python production web runtime

**Project Type**: Python ML-backed web application with batch-analysis CLI

**Performance Goals**: 95% of successful approved releases become healthy within 10 minutes; health verification must complete before release success is reported; allow up to 120 seconds for CPU-backed photo review requests

**Constraints**: One primary production environment; one review at a time due to the current global review lock; no writable persistent storage required by the web process; credentials must remain outside source and logs; production deployments must not be cancelled mid-flight

**Scale/Scope**: Version 1 covers one Python web service, one production environment, pull-request validation, protected-branch validation, approved production deployment, health verification, and rollback; preview environments and multi-region deployment are out of scope

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

The repository constitution is an uninstantiated template: it defines no enforceable project principles, additional constraints, or governance rules. No constitution-specific gates apply. The plan nevertheless preserves the specification's security, validation, deployment approval, and rollback requirements as design constraints.

**Gate status**: PASS. No violations require justification.

## Project Structure

### Documentation (this feature)

```text
specs/004-github-actions-deployment/
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
.github/
└── workflows/
    ├── ci.yml                    # Pull-request and protected-branch validation
    ├── deploy-production.yml     # Approved, immutable production deployment
    └── rollback-production.yml   # Protected rollback to a healthy revision

src/
├── upload_server.py              # Live HTTP entry point and health contract
├── upload_service.py              # Request-scoped photo review behavior
└── generated/                    # Spec-generated contracts, checked for drift

scripts/
└── spec.py                       # Specification validation and generation

tests/
├── test_upload_server.py
├── test_upload_service.py
└── ...                           # Existing unittest acceptance coverage

specs/004-github-actions-deployment/
├── contracts/
├── data-model.md
├── quickstart.md
├── research.md
└── plan.md
```

**Structure Decision**: Keep the existing single-project layout. Add workflow definitions under `.github/workflows/`, extend the web server with a provider-neutral health/version surface as needed, and add deployment-focused tests alongside the existing `unittest` suite. Do not introduce a framework, database, or separate frontend/backend project.

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| None | No constitution violations identified | Not applicable |
