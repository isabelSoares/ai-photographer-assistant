# Research: Add AI Assistant Link

## Decision: Place the invitation in the homepage hero action group

**Rationale**: `ts-app/src/components/about-me/AboutMe.tsx` already has an `.about-me-actions` group containing the primary experience link and contact action. The hero is the portfolio's main discovery surface and is more appropriate than adding another dense top-bar control.

**Alternatives considered**: A new top-bar item was rejected because the existing navigation is already dense on narrow screens. A new portfolio route was rejected because the assistant is a separate application.

## Decision: Use a native external anchor that opens a new tab

**Rationale**: A native anchor preserves keyboard navigation, copy-link behavior, browser controls, and no-JavaScript operation. `target="_blank"` with `rel="noopener noreferrer"` keeps the portfolio available and prevents opener access.

**Alternatives considered**: `window.open()` was rejected because it weakens normal link behavior. React Router `Link` was rejected because the destination is outside the portfolio application. Same-tab navigation was rejected because the requested progression keeps the portfolio available for return navigation.

## Decision: Configure one public URL with CRA environment configuration

**Rationale**: The website uses Create React App, so `REACT_APP_AI_ASSISTANT_URL` is the project-appropriate build-time configuration convention. The URL is public after bundling and therefore contains no secret. A single value prevents the destination from being duplicated across JSX and deployment documentation.

**Alternatives considered**: Hardcoding the URL in `AboutMe.tsx` was rejected because changing the Render URL would require source edits. A runtime `config.json` was rejected because it adds an extra request and failure mode to a static site.

## Decision: Validate the production destination before Pages publication

**Rationale**: A missing or placeholder assistant link is a release defect. A Node validation script can parse the URL and reject non-HTTPS, local, private, example, repository, or placeholder destinations before `npm run build` and Pages publication.

**Alternatives considered**: Relying on manual review was rejected because it cannot reliably detect stale or placeholder values. Requiring a live network request in every build was rejected because third-party availability and DNS failures would create false negatives; availability is a separate smoke check.

## Decision: Keep analytics optional and non-blocking

**Rationale**: The link must work without analytics, consent tooling, or third-party scripts. If the existing website later enables analytics, it may record one aggregate outbound-click event without collecting assistant uploads or results.

**Alternatives considered**: Adding analytics as part of this feature was rejected because it expands privacy, consent, and performance scope before early interest has been established.

## Decision: Keep the assistant separately deployed

**Rationale**: The existing Python/YOLO application requires server-side execution and is not suitable for GitHub Pages. A link creates value with no cross-origin API, authentication, shared state, or backend coupling.

**Alternatives considered**: Embedding the upload flow or integrating an API was deferred until usage feedback justifies the additional deployment and security complexity.

## Configuration Contract

The production Pages workflow will provide `AI_ASSISTANT_URL` as a repository or environment variable and map it to `REACT_APP_AI_ASSISTANT_URL` for the CRA build. It must be a public HTTPS URL for the separately deployed assistant, not the GitHub repository URL.
