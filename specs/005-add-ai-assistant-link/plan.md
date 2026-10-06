# Implementation Plan: Add AI Assistant Link

**Branch**: `005-add-ai-assistant-link` | **Date**: 2026-10-06 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `/specs/005-add-ai-assistant-link/spec.md`

## Summary

Add a prominent external link to the AI Photographer Assistant in the existing portfolio homepage hero. The link will be a native accessible anchor that opens the separately deployed assistant in a new tab, while the destination is supplied once through the React production configuration. The `myWebSite` GitHub Pages build will reject missing or placeholder destinations before publishing, and the feature will not introduce API integration or shared application state.

## Technical Context

<!--
  ACTION REQUIRED: Replace the content in this section with the technical details
  for the project. The structure here is presented in advisory capacity to guide
  the iteration process.
-->

**Language/Version**: TypeScript 4.9 with React 17 and Create React App 5; Node.js 24 in the existing Pages workflow

**Primary Dependencies**: Existing React Router, Material UI, Font Awesome, Testing Library, and `react-scripts`; no new runtime dependency

**Storage**: N/A; the destination is a public build-time configuration value

**Testing**: `npm test -- --watchAll=false`, `npm run build`, and a deterministic assistant-URL validation script

**Target Platform**: Static GitHub Pages site at `https://isabelsoares.github.io/myWebSite/`, desktop and mobile browsers

**Project Type**: Static React portfolio website

**Performance Goals**: The invitation must not add a network request or block initial portfolio rendering; production build validation must complete within the existing Pages workflow limits

**Constraints**: External URL must be a public HTTPS URL, never a placeholder or repository URL; no secrets in client configuration; preserve the existing GitHub Pages subpath and light/dark themes; keep the assistant separately deployed

**Scale/Scope**: One homepage invitation, one configured destination, one optional outbound-click analytics event, one GitHub Pages build/deploy workflow; embedded upload and API integration are out of scope

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

The repository constitution is an uninstantiated template and defines no enforceable principles, constraints, or governance rules. No constitution-specific gates apply. The design still preserves the specification's accessibility, privacy, production-configuration, and separate-deployment requirements.

**Gate status**: PASS. No violations require justification.

## Project Structure

### Documentation (this feature)

```text
specs/005-add-ai-assistant-link/
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
/Users/isabelsoares/Repos/myWebSite/
├── .github/workflows/deploy-pages.yml       # URL validation and Pages deployment
└── ts-app/
    ├── scripts/validate-assistant-url.js    # Production destination validation
    ├── src/
    │   ├── config/assistant.ts               # Single public destination value
    │   ├── components/about-me/AboutMe.tsx   # Homepage invitation
    │   ├── components/about-me/AboutMe.scss  # Responsive/focus styling
    │   └── App.test.tsx                      # Homepage link coverage
    └── package.json                           # Validation script
```

**Structure Decision**: Implement the feature in the sibling `myWebSite` repository, not in the Python assistant repository. Reuse the existing homepage hero action group and styling. Keep the assistant URL in one CRA `REACT_APP_AI_ASSISTANT_URL` value, validate it before a production Pages build, and pass the repository's public `AI_ASSISTANT_URL` variable into the workflow. Use a native `<a>` rather than React Router because the destination is external.

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| None | No constitution violations identified | Not applicable |
