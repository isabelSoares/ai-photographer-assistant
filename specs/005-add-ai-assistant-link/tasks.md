---

description: "Task list for Add AI Assistant Link"

---

# Tasks: Add AI Assistant Link

**Input**: Design documents from `/specs/005-add-ai-assistant-link/`

**Prerequisites**: `plan.md`, `spec.md`, `research.md`, `data-model.md`, `contracts/assistant-link.md`, and `quickstart.md`

**Implementation repository**: `/Users/isabelsoares/Repos/myWebSite`

**Tests**: Included because the feature specification defines link behavior, production URL validation, accessibility outcomes, and GitHub Pages release checks.

**Organization**: Tasks are grouped by user story while explicitly naming the sibling repository files that implement the feature.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel when tasks touch different files and have no incomplete dependency.
- **[Story]**: Required only for user-story phases and maps to `[US1]`, `[US2]`, or `[US3]`.
- Every task includes an exact file path in `/Users/isabelsoares/Repos/myWebSite`.

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Establish the target repository configuration surface without changing the visitor experience.

- [x] T001 Verify `/Users/isabelsoares/Repos/myWebSite` is clean or record unrelated worktree changes before editing the sibling repository.
- [x] T002 [P] Add the `validate:assistant-url` npm script to `/Users/isabelsoares/Repos/myWebSite/ts-app/package.json` without adding a runtime dependency.
- [x] T003 [P] Update `/Users/isabelsoares/Repos/myWebSite/.github/workflows/deploy-pages.yml` to pass the public `AI_ASSISTANT_URL` repository variable as `REACT_APP_AI_ASSISTANT_URL` to validation and production build steps.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Define and test the single public assistant destination before homepage work begins.

**Checkpoint**: The target repository can deterministically accept a real public assistant URL and reject unsafe or placeholder destinations.

- [x] T004 [P] Add validator tests in `/Users/isabelsoares/Repos/myWebSite/ts-app/scripts/validate-assistant-url.test.js` covering missing values, non-absolute URLs, non-HTTPS URLs, localhost, private/loopback hosts, example domains, placeholders, GitHub repository URLs, valid HTTPS roots, and valid HTTPS paths.
- [x] T005 Implement the URL validator in `/Users/isabelsoares/Repos/myWebSite/ts-app/scripts/validate-assistant-url.js` using the platform URL parser; require an absolute `https:` URL and reject values matching the contract's placeholder, local, example, private, and repository rules.
- [x] T006 [P] Create the single destination export in `/Users/isabelsoares/Repos/myWebSite/ts-app/src/config/assistant.ts`, reading `REACT_APP_AI_ASSISTANT_URL` and using only a clearly non-production fallback for local tests.
- [x] T007 Add deterministic validator execution to `/Users/isabelsoares/Repos/myWebSite/ts-app/package.json` and ensure validation reports a concise reason without printing unrelated environment variables.

---

## Phase 3: User Story 1 - Discover the AI Photographer Assistant (Priority: P1) 🎯 MVP

**Goal**: Portfolio visitors can see and understand a prominent invitation to try the separate assistant.

**Independent Test**: Render the homepage and verify a descriptive assistant link is visible, keyboard-discoverable, and present at mobile-sized layouts without changing existing portfolio navigation.

### Tests for User Story 1

- [x] T008 [P] [US1] Extend `/Users/isabelsoares/Repos/myWebSite/ts-app/src/App.test.tsx` to find the assistant invitation by accessible link name and verify it renders alongside the existing homepage content.

### Implementation for User Story 1

- [x] T009 [US1] Add the visible `Try the AI Photographer Assistant` native anchor to `/Users/isabelsoares/Repos/myWebSite/ts-app/src/components/about-me/AboutMe.tsx` in the existing `.about-me-actions` hero group.
- [x] T010 [US1] Add responsive and keyboard-focus styling for the assistant invitation in `/Users/isabelsoares/Repos/myWebSite/ts-app/src/components/about-me/AboutMe.scss`, preserving light/dark theme variables and preventing narrow-screen overflow.

**Checkpoint**: User Story 1 is complete when visitors can find and focus the invitation on the homepage without relying on JavaScript navigation.

---

## Phase 4: User Story 2 - Open the Deployed Assistant (Priority: P1)

**Goal**: Selecting the invitation opens the configured deployed assistant, not the source repository, while preserving the portfolio page.

**Dependencies**: Requires the destination contract from Phase 2 and the visible invitation from User Story 1.

**Independent Test**: Render the homepage with a known HTTPS assistant URL and verify the link's destination, new-tab behavior, opener protection, and production build validation.

### Tests for User Story 2

- [x] T011 [P] [US2] Extend `/Users/isabelsoares/Repos/myWebSite/ts-app/src/App.test.tsx` to verify the assistant link uses the configured external URL, `target="_blank"`, `rel="noopener noreferrer"`, and text that communicates separate navigation.
- [x] T012 [P] [US2] Add production configuration and generated-bundle assertions in `/Users/isabelsoares/Repos/myWebSite/ts-app/scripts/validate-assistant-url.test.js` for the accepted URL contract and rejection of the GitHub repository or placeholder destination.

### Implementation for User Story 2

- [x] T013 [US2] Wire the assistant destination export from `/Users/isabelsoares/Repos/myWebSite/ts-app/src/config/assistant.ts` into the anchor in `/Users/isabelsoares/Repos/myWebSite/ts-app/src/components/about-me/AboutMe.tsx` without duplicating the URL literal.
- [x] T014 [US2] Add `AI_ASSISTANT_URL` environment mapping, validator execution, and production build environment configuration to `/Users/isabelsoares/Repos/myWebSite/.github/workflows/deploy-pages.yml`, preventing Pages publication when the destination is invalid.
- [x] T015 [US2] Update `/Users/isabelsoares/Repos/myWebSite/README.md` with the public assistant destination configuration, required `AI_ASSISTANT_URL` repository variable, and deployment verification steps.

**Checkpoint**: User Stories 1 and 2 are complete when a configured production build publishes a working external link and rejects unsafe destinations before Pages deployment.

---

## Phase 5: User Story 3 - Measure Early Interest (Priority: P2)

**Goal**: Preserve an optional, privacy-safe way to identify assistant-link interest without making analytics a navigation dependency.

**Dependencies**: Requires User Story 2's stable assistant anchor and production destination.

**Independent Test**: Verify the link works with analytics unavailable and, when an existing analytics integration is enabled later, exposes one stable interaction name without carrying photo or result data.

### Tests for User Story 3

- [x] T016 [P] [US3] Add an assertion in `/Users/isabelsoares/Repos/myWebSite/ts-app/src/App.test.tsx` that the assistant invitation exposes the stable `ai_assistant_link_click` interaction metadata without requiring an analytics library.

### Implementation for User Story 3

- [x] T017 [US3] Add non-blocking `data-analytics-event="ai_assistant_link_click"` metadata to the assistant anchor in `/Users/isabelsoares/Repos/myWebSite/ts-app/src/components/about-me/AboutMe.tsx` and do not add a new analytics dependency.
- [x] T018 [US3] Document optional aggregate click measurement, privacy boundaries, and analytics-disabled behavior in `/Users/isabelsoares/Repos/myWebSite/README.md`.

**Checkpoint**: All user stories are complete when the link is discoverable, opens the separately deployed assistant, and remains functional without analytics.

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Validate the cross-repository handoff, accessibility, build output, and release safety.

- [x] T019 [P] Add a visible new-context focus style and verify contrast in `/Users/isabelsoares/Repos/myWebSite/ts-app/src/components/about-me/AboutMe.scss` for both light and dark theme variables.
- [x] T020 [P] Update `/Users/isabelsoares/Repos/myWebSite/.github/workflows/deploy-pages.yml` to run on pull requests for validation while limiting the actual Pages deployment job to successful `main` pushes or explicit manual dispatch.
- [x] T021 Run `npm ci`, `npm run validate:assistant-url`, `npm test -- --watchAll=false`, and `npm run build` from `/Users/isabelsoares/Repos/myWebSite/ts-app` with a real HTTPS assistant URL and record results in `/Users/isabelsoares/Repos/ai-photographer-assistant/specs/005-add-ai-assistant-link/quickstart.md`.
- [x] T022 Run the negative URL cases from `/Users/isabelsoares/Repos/ai-photographer-assistant/specs/005-add-ai-assistant-link/quickstart.md` against `/Users/isabelsoares/Repos/myWebSite/ts-app/scripts/validate-assistant-url.js` and confirm production publication is blocked for each invalid destination.
- [x] T023 Review the generated Pages artifact from `/Users/isabelsoares/Repos/myWebSite/ts-app/build` to confirm the verified HTTPS destination is present, placeholders are absent, the existing Pages subpath still builds, and no secrets are bundled.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Phase 1 Setup**: T001 precedes edits; T002 and T003 can proceed in parallel after repository access is verified.
- **Phase 2 Foundational**: Depends on Phase 1; T004 should be written before T005, while T006 can proceed in parallel because it touches a separate source file.
- **Phase 3 User Story 1**: Depends on Phase 2; T008 is written before T009, and T010 follows the component markup.
- **Phase 4 User Story 2**: Depends on User Story 1; T011 and T012 can be written in parallel, then T013 and T014 integrate the tested contract.
- **Phase 5 User Story 3**: Depends on User Story 2; T016 precedes T017, while T018 can proceed after the event name is fixed.
- **Phase 6 Polish**: Depends on the desired user stories; T019 and T020 can proceed in parallel, while T021 through T023 are final validation tasks.

### User Story Dependencies

- **User Story 1 (P1)**: Requires Phase 2 destination configuration; this is the MVP.
- **User Story 2 (P1)**: Requires User Story 1's visible invitation and Phase 2 validator.
- **User Story 3 (P2)**: Requires User Story 2's stable anchor; it does not require an analytics provider.

### Parallel Opportunities

- T002 and T003 can run in parallel after T001.
- T004 and T006 can be prepared in parallel; T005 follows the validator tests.
- T011 and T012 can be prepared in parallel before T013/T014 integration.
- T018 and T019 can proceed in parallel after the analytics metadata and styling decisions are fixed.
- T019 and T020 can proceed in parallel; T021 and T022 can run in parallel after implementation, with T023 after both.

## Parallel Example: User Story 1

```text
Task T008: Extend homepage coverage in /Users/isabelsoares/Repos/myWebSite/ts-app/src/App.test.tsx
Task T010: Add responsive/focus styling in /Users/isabelsoares/Repos/myWebSite/ts-app/src/components/about-me/AboutMe.scss
```

T009 must define the anchor markup before T010's final selectors and before User Story 2 wires its destination.

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phases 1 and 2.
2. Complete User Story 1 with the hero invitation and accessibility styling.
3. Run the homepage test at desktop and mobile widths.
4. Stop with a visible, non-functional-safe link surface ready for the verified assistant URL.

### Incremental Delivery

1. Add User Story 1 to make the assistant discoverable.
2. Add User Story 2 to connect the verified public destination and release validation.
3. Add User Story 3 metadata and documentation without introducing analytics infrastructure.
4. Run the Pages build and artifact checks before publishing to `main`.

## Notes

- The tasks modify `/Users/isabelsoares/Repos/myWebSite`; the specification artifacts remain in the assistant repository for cross-repository traceability.
- `REACT_APP_AI_ASSISTANT_URL` is public build output, not a secret. It must contain only the assistant URL.
- A real Render URL is required before production Pages publication; the placeholder from the original request must never be used.
