---
description: "Task list for Cloudflare Photo Assistant feature"
---

# Tasks: Cloudflare Photo Assistant

**Input**: Design documents from `/specs/007-cloudflare-photo-assistant/`

**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/photo-assistant-api.md

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel.
- **[Story]**: User story label (US1, US2, US3).

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [x] T001 Create feature directory `specs/007-cloudflare-photo-assistant/` and design documents
- [x] T002 Create Worker project structure under `worker/`
- [x] T003 Create React component structure under `web-component/`
- [x] T004 [P] Add `worker/package.json` with Wrangler and TypeScript dependencies
- [x] T005 [P] Add `worker/tsconfig.json` and `worker/wrangler.toml`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before user stories

- [x] T006 Configure Worker CORS and request validation in `worker/src/index.ts`
- [x] T007 Implement client-side image resize helper for `PhotoAssistant.tsx`
- [x] T008 Define shared guidance result types and constants in `worker/src/types.ts`

**Checkpoint**: Foundation ready - user story implementation can now begin.

---

## Phase 3: User Story 1 - Upload and Receive Suggestions (Priority: P1) 🎯 MVP

**Goal**: A visitor can upload a photo and receive actionable photography suggestions.

**Independent Test**: Open the portfolio, upload a supported photo, and see a summary with at least one tip.

### Implementation for User Story 1

- [x] T009 [US1] Integrate Workers AI object detection (`@cf/facebook/detr-resnet-50`) in `worker/src/index.ts`
- [x] T010 [US1] Integrate Workers AI scene classification (`@cf/microsoft/resnet-50`) in `worker/src/index.ts`
- [x] T011 [US1] Implement rule-based tip generator in `worker/src/tips.ts`
- [x] T012 [US1] Build `PhotoAssistant.tsx` upload flow and result rendering
- [x] T013 [US1] Add default styles in `web-component/photo-assistant.scss`
- [x] T014 [US1] Handle backend errors and unsupported files in `PhotoAssistant.tsx`

**Checkpoint**: User Story 1 is fully functional and testable independently.

---

## Phase 4: User Story 2 - Integrate into React Portfolio with Custom Design (Priority: P2)

**Goal**: The assistant matches the portfolio design and works on mobile.

**Independent Test**: View the portfolio on desktop and mobile; the assistant styling is indistinguishable from the rest of the page.

### Implementation for User Story 2

- [x] T015 [US2] Refactor `PhotoAssistant.tsx` to expose CSS variables for theming
- [x] T016 [US2] Add responsive layout rules in `web-component/photo-assistant.scss`
- [x] T017 [US2] Write `docs/integration.md` with copy-and-paste instructions for `myWebSite`

**Checkpoint**: User Story 2 works independently and blends into the portfolio.

---

## Phase 5: User Story 3 - Always-Available Free Backend (Priority: P2)

**Goal**: The backend never sleeps and stays within free-tier limits.

**Independent Test**: Upload a photo after a long idle period; response arrives without delay.

### Implementation for User Story 3

- [x] T018 [US3] Optimize Worker CPU usage by keeping image processing minimal in `worker/src/index.ts`
- [x] T019 [US3] Add client-side resize limits to keep uploads small in `PhotoAssistant.tsx`
- [x] T020 [US3] Document free-tier limits and CORS origin setup in `docs/integration.md`

**Checkpoint**: Backend responds immediately after idle periods and remains within free quotas.

---

## Phase 6: Environment & Deployment

**Purpose**: Ensure the maintainer can deploy the solution

- [x] T021 Add Node.js v22+ update instructions and Wrangler login task to `docs/integration.md`
- [x] T022 Verify `worker/` builds with `wrangler deploy --dry-run` (passed; `npx tsc --noEmit` also passed)
- [x] T023 Update root `README.md` with a link to the new feature docs

---

## Phase 7: Pipeline Migration — Render to Cloudflare (Priority: P1)

**Purpose**: Replace the Render auto-deploy path with automatic Cloudflare Worker deployment

**Goal**: Every merge to `main` automatically deploys the Cloudflare Worker after CI passes.

**Independent Test**: Push to `main`, wait for CI success, confirm the Cloudflare workflow runs and the Worker is updated.

### Remove Render

- [x] T024 Delete `.github/workflows/deploy-render.yml`
- [x] T025 [P] Remove Render references from `docs/deployment.md`
- [x] T026 [P] Remove Render references from `README.md`
- [x] T027 [P] Remove Render-specific assertions from `tests/test_deployment_workflows.py`

### Add Cloudflare Auto-Deploy

- [x] T028 [P] Verify `worker/package.json` exposes `npm run typecheck`
- [x] T029 Update `.github/workflows/ci.yml` to run Worker typecheck
- [x] T030 Create `.github/workflows/deploy-cloudflare.yml` with `workflow_run` trigger after CI success on `main`
- [x] T031 Pin `cloudflare/wrangler-action` to immutable SHA in `.github/workflows/deploy-cloudflare.yml`
- [x] T032 Configure `CLOUDFLARE_API_TOKEN` and `CLOUDFLARE_ACCOUNT_ID` in `.github/workflows/deploy-cloudflare.yml`
- [x] T033 Add Wrangler deploy step scoped to `worker/` in `.github/workflows/deploy-cloudflare.yml`

### Validation & Documentation

- [x] T034 [P] Add Cloudflare workflow assertions to `tests/test_deployment_workflows.py`
- [x] T035 [P] Update `docs/deployment.md` with Cloudflare Worker deployment flow and required GitHub configuration
- [x] T036 [P] Update `README.md` continuous-delivery section
- [x] T037 Run `python -m unittest discover -s tests -v` to verify test updates pass

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies.
- **Foundational (Phase 2)**: Depends on Setup.
- **User Story 1 (Phase 3)**: Depends on Foundational.
- **User Story 2 (Phase 4)**: Depends on User Story 1.
- **User Story 3 (Phase 5)**: Depends on User Story 1.
- **Environment & Deployment (Phase 6)**: Depends on all stories.

### Parallel Opportunities

- T004 and T005 can run in parallel.
- T009, T010, and T011 can run in parallel after foundation.
- T015, T016, and T017 can run in parallel.
- T018, T019, and T020 can run in parallel.

### MVP Scope

Complete Setup, Foundational, and User Story 1 to have a working assistant. Then add styling/integration (US2) and backend reliability polish (US3).

---

## Notes

- No automated tests are required for v1; validation is manual via `quickstart.md`.
- The maintainer must update Node.js to v22+ before Wrangler will work.
- The Worker must be redeployed after any `wrangler.toml` change.
