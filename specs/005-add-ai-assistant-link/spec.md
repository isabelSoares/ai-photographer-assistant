# Feature Specification: Add AI Assistant Link

**Feature Branch**: `005-add-ai-assistant-link`

**Created**: 2026-10-06

**Status**: Draft

**Input**: User description: "Deploy the assistant separately, then add a button like: <a href=\"https://your-ai-assistant.onrender.com\" class=\"ai-assistant-button\"> Try the AI Photographer Assistant </a> Use the assistant’s deployed URL, not the GitHub repository URL. Tradeoff Users leave the main website and open a separate application. Later, if you want a seamless experience, integrate the upload experience directly using an API. Recommended progression: deploy the AI assistant separately, add a button to the existing website, collect feedback, and integrate the upload experience later if users need it. Take into consideration the repository /Users/isabelsoares/Repos/myWebSite."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Discover the AI Photographer Assistant (Priority: P1)

As a visitor to the portfolio website, I want to see a clear invitation to try the AI Photographer Assistant so that I can discover the related project without searching through the repository.

**Why this priority**: The link is the smallest complete feature and creates a direct path from the existing audience to the assistant.

**Independent Test**: A tester can open the published portfolio on desktop and mobile-sized screens, identify the assistant invitation, and understand what will happen when selecting it.

**Acceptance Scenarios**:

1. **Given** a visitor views the portfolio, **When** the page finishes loading, **Then** a clearly labeled AI Photographer Assistant invitation is visible in an appropriate portfolio section.
2. **Given** the invitation is visible, **When** the visitor reads its label, **Then** the label communicates that selecting it opens the AI Photographer Assistant rather than another portfolio page.
3. **Given** the portfolio is viewed on a mobile-sized screen, **When** the visitor scans the page, **Then** the invitation remains readable, usable, and does not cause horizontal overflow.

---

### User Story 2 - Open the Deployed Assistant (Priority: P1)

As a visitor who selects the invitation, I want to reach the deployed AI Photographer Assistant so that I can use the project instead of landing on its source repository.

**Why this priority**: A visible link has no user value unless it reaches the live assistant application.

**Independent Test**: A tester can select the invitation from the published portfolio and verify that the resulting page is the configured deployed assistant URL and loads the assistant interface.

**Acceptance Scenarios**:

1. **Given** the assistant has a configured public deployment URL, **When** the visitor selects the invitation, **Then** the browser opens that deployed URL and not the GitHub source repository.
2. **Given** the visitor opens the assistant, **When** the assistant is loading or temporarily unavailable, **Then** the portfolio remains usable and the visitor can return to it without losing the portfolio page.
3. **Given** the deployment URL changes, **When** the maintainer updates the configured destination, **Then** the published invitation uses the new destination without changing its user-facing label.

---

### User Story 3 - Measure Early Interest (Priority: P2)

As the project maintainer, I want to understand whether visitors select the assistant invitation so that I can decide whether deeper website integration is worthwhile.

**Why this priority**: Measuring interest supports the recommended progression without forcing an API integration before there is evidence of demand.

**Independent Test**: A tester can select the invitation in a supported analytics or privacy-safe observation setup and verify that the maintainer can distinguish assistant link interest from ordinary portfolio navigation, when analytics are enabled.

**Acceptance Scenarios**:

1. **Given** analytics are enabled for the portfolio, **When** a visitor selects the assistant invitation, **Then** the interaction can be identified as an assistant-link selection without recording uploaded photos or sensitive assistant data.
2. **Given** analytics are disabled or unavailable, **When** a visitor selects the invitation, **Then** navigation to the assistant still works normally.
3. **Given** early feedback does not justify deeper integration, **When** the maintainer reviews the feature, **Then** the portfolio can continue using the separate assistant link without requiring an API migration.

### Edge Cases

- The assistant deployment URL is missing, malformed, or still a placeholder when the website is prepared for publication.
- The assistant is temporarily sleeping, unavailable, or returns an error after the visitor selects the link.
- A visitor opens the portfolio with JavaScript disabled.
- The visitor uses keyboard navigation, a screen reader, or a narrow mobile viewport.
- The assistant deployment URL changes after the portfolio has been published.
- Analytics are blocked by browser settings, consent choices, or an unavailable analytics service.
- The portfolio is deployed from a pull request or preview build and must not point visitors to a private or test assistant deployment.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The portfolio MUST provide a clearly labeled invitation to try the AI Photographer Assistant.
- **FR-002**: The invitation MUST link to the configured public deployment of the AI Photographer Assistant and MUST NOT link to the assistant's source repository as its primary destination.
- **FR-003**: The invitation MUST use a user-facing label that communicates the assistant action, such as "Try the AI Photographer Assistant".
- **FR-004**: The invitation MUST be usable with mouse, keyboard, touch, and assistive technology.
- **FR-005**: The invitation MUST remain readable and usable on desktop and mobile-sized screens without causing horizontal overflow or obscuring existing portfolio content.
- **FR-006**: The portfolio MUST preserve its current navigation and content when a visitor selects or returns from the assistant.
- **FR-007**: The assistant destination MUST be maintainable as a single configured value so a deployment URL change does not require changing the invitation label or duplicating the URL across unrelated content.
- **FR-008**: The published portfolio MUST NOT expose a placeholder, private deployment URL, local development URL, or GitHub repository URL as the production assistant destination.
- **FR-009**: If analytics are enabled, the portfolio MAY record assistant-invitation selections as an aggregate navigation interaction, but MUST NOT collect uploaded photos or assistant-result content through this link feature.
- **FR-010**: If the assistant is unavailable, the portfolio MUST remain functional and MUST NOT depend on a successful assistant response to load or navigate its own content.
- **FR-011**: The feature MUST preserve the assistant as a separately deployed application; direct photo-upload integration into the portfolio is out of scope for this increment.
- **FR-012**: The production website MUST publish the invitation only after the assistant destination has been verified as publicly reachable and intended for visitors.

### Key Entities *(include if feature involves data)*

- **Assistant Destination**: The configured public URL of the separately deployed AI Photographer Assistant, including its environment and publication status.
- **Assistant Invitation**: The visible portfolio call to action, including its label, destination, accessibility name, and visual state.
- **Navigation Interaction**: An optional aggregate record that a visitor selected the assistant invitation, without containing photos or assistant results.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: At least 95% of usability testers can locate the assistant invitation within 10 seconds of opening the portfolio.
- **SC-002**: At least 98% of valid assistant-invitation selections from the published portfolio reach the configured assistant URL rather than the source repository or an error caused by the portfolio link.
- **SC-003**: 100% of tested desktop, tablet, and mobile viewport sizes keep the invitation visible, readable, keyboard-accessible, and free of horizontal overflow.
- **SC-004**: 100% of production publication checks reject a missing, placeholder, private, local, or repository destination before the portfolio is published.
- **SC-005**: At least 90% of usability testers understand that selecting the invitation opens a separate AI Photographer Assistant application.
- **SC-006**: When analytics are enabled, the maintainer can review assistant-invitation selections separately from other navigation interactions within one reporting period.
- **SC-007**: The portfolio remains fully usable in 100% of tests where the assistant is unavailable after the invitation is selected.

## Assumptions

- The existing website is the static React portfolio in `/Users/isabelsoares/Repos/myWebSite`, published at `https://isabelsoares.github.io/myWebSite/`.
- The AI Photographer Assistant remains in `/Users/isabelsoares/Repos/ai-photographer-assistant` and is deployed separately before the production portfolio link is enabled.
- The assistant deployment will provide a stable public HTTPS URL; the exact Render URL is not yet known and will be configured before publication.
- The invitation opens the separate assistant in a new browser tab by default so visitors can return to the portfolio easily; the portfolio remains available in the original tab.
- The production portfolio uses one public assistant destination; local and preview builds may use no destination or a clearly labeled test destination that is never published as production.
- Analytics are optional and follow the portfolio's existing privacy and consent practices; this feature does not introduce a new analytics platform.
- Version 1 measures interest through a separate link; embedded upload, shared authentication, shared state, and API-based integration are future work.
