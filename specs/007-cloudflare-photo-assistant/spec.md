# Feature Specification: Cloudflare Photo Assistant

**Feature Branch**: `007-cloudflare-photo-assistant`

**Created**: 2026-10-09

**Status**: Draft

**Input**: User description: "Render free plan does not work well for the AI photo assistant. Is Hugging Face Spaces better? When clicking 'Try AI photo assistant', upload works and reviews the photo, but suggestions are not visible. How can the project see photo suggestions? Give an efficient free solution to upload images and integrate into my website."

## Decisions from Clarifications

- **Q1**: No guaranteed Hugging Face account in good standing → use Cloudflare instead of Hugging Face Spaces.
- **Q2**: Assistant must be embedded directly in the portfolio page, not opened in a separate tab.
- **Q3**: Open to managed AI inference, replacing the self-hosted YOLO pipeline.
- **Q4**: Portfolio is built with React and hosted on GitHub Pages; keep it there.
- **Q5**: No sleeping/cold-start delays allowed → use Cloudflare Workers (no sleep).
- **Q6**: Privacy is acceptable as long as uploaded photos are not retained after analysis.
- **Q7**: Keep v1 simple; no Turnstile or abuse protection in the first version.

## Problem Statement

The current Render Free deployment is too slow and unreliable for CPU-heavy photo analysis. Users can upload a photo but never see the suggestions because the service times out, spins down, or loses in-memory jobs. The project needs a free, no-sleep backend and a seamless embedded UI that matches the portfolio.

## Goals

- Provide a fast, always-available photo assistant embedded in the React portfolio.
- Remove the need to host a YOLO model on a low-resource free tier.
- Keep uploaded photos ephemeral and not stored by the application.
- Stay within free-tier limits of Cloudflare Workers AI.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Upload and Receive Suggestions (Priority: P1)

As a portfolio visitor, I want to upload a photo in an embedded assistant and receive practical photography suggestions, so that I can improve my next shots without leaving the site.

**Why this priority**: This is the core user value of the feature.

**Independent Test**: A tester opens the portfolio, uploads a supported photo, and sees a summary with at least one actionable tip.

**Acceptance Scenarios**:

1. **Given** the assistant is visible on the portfolio, **When** the visitor selects a supported photo, **Then** the photo is accepted and the visitor sees a clear loading state.
2. **Given** the photo is accepted, **When** analysis completes, **Then** the visitor sees a human-readable summary and at least one tip.
3. **Given** analysis cannot produce specific guidance, **When** the result is returned, **Then** the visitor sees a useful general tip and an uncertainty notice.
4. **Given** the visitor selects an unsupported, corrupted, or oversized file, **When** they submit it, **Then** they see a plain-language error and can try again.

### User Story 2 - Integrate into React Portfolio with Custom Design (Priority: P2)

As the site maintainer, I want the assistant to look like part of my React portfolio on GitHub Pages, so that the experience feels cohesive and professional.

**Why this priority**: A mismatched embedded UI would hurt the portfolio's quality perception.

**Independent Test**: A tester views the portfolio on desktop and mobile and cannot distinguish the assistant from the rest of the page styling without inspecting the code.

**Acceptance Scenarios**:

1. **Given** the assistant is embedded in a React page, **When** the page loads, **Then** the component renders using the portfolio's fonts, colors, and spacing.
2. **Given** the visitor uses a mobile-sized screen, **When** they interact with the assistant, **Then** the layout remains usable without horizontal overflow.
3. **Given** the maintainer updates portfolio styles, **When** they change the CSS variables used by the assistant, **Then** the assistant updates to match without code changes.

### User Story 3 - Always-Available Free Backend (Priority: P2)

As the site maintainer, I want the backend to respond quickly and never sleep, so that visitors always get a result instead of a timeout or cold-start delay.

**Why this priority**: The Render Free sleeping behavior was the root cause of the missing suggestions.

**Independent Test**: A tester uploads a photo after the site has had no traffic for a long time and still receives a result within a few seconds.

**Acceptance Scenarios**:

1. **Given** the portfolio has had no visitors for many hours, **When** a visitor uploads a photo, **Then** the backend responds immediately without a wake-up delay.
2. **Given** the backend is under normal load, **When** a visitor uploads a photo, **Then** the response returns within 10 seconds.
3. **Given** the daily free quota is not exhausted, **When** a visitor uploads a photo, **Then** the request succeeds without errors.

### Edge Cases

- Visitor selects a file that is not an image.
- Visitor selects an image larger than the client-side resize limit.
- Visitor loses connection during upload.
- The backend returns an empty detection/classification result.
- The backend returns a low-confidence result.
- The visitor refreshes the page while analysis is in progress.
- The visitor uploads a second photo before the first result is displayed.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The assistant MUST be embeddable as a React component in the portfolio.
- **FR-002**: The component MUST accept a supported image file from the visitor's device.
- **FR-003**: The component MUST resize and compress the image in the browser before sending it to the backend.
- **FR-004**: The component MUST display a loading state while analysis is in progress.
- **FR-005**: The component MUST render a summary, tips, detected subjects, and scene labels returned by the backend.
- **FR-006**: The component MUST display plain-language errors when uploads or analysis fail.
- **FR-007**: The component MUST allow the visitor to upload a new photo after a result or error.
- **FR-008**: The backend MUST expose a single POST endpoint that accepts a resized image.
- **FR-009**: The backend MUST call Cloudflare Workers AI for object detection and scene classification.
- **FR-010**: The backend MUST generate at least one actionable photography tip from the AI outputs.
- **FR-011**: The backend MUST return results in a stable JSON shape matching the existing `PhotoGuidanceResult`.
- **FR-012**: The backend MUST set CORS headers to allow requests only from the configured portfolio origin.
- **FR-013**: The backend MUST NOT persist uploaded images or results.
- **FR-014**: The backend MUST handle unsupported or malformed input with a clear error response.

### Non-Functional Requirements

- **NFR-001**: The backend MUST not sleep between requests.
- **NFR-002**: The backend MUST respond within 10 seconds under normal conditions.
- **NFR-003**: The backend MUST stay within Cloudflare Workers Free limits (100,000 requests/day, 10 ms CPU/invocation, 10,000 AI neurons/day).
- **NFR-004**: The component MUST work on desktop and mobile viewports.
- **NFR-005**: The component MUST add no more than one lightweight JavaScript file and one CSS file to the portfolio build.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: 95% of supported uploads produce a visible suggestion within 10 seconds.
- **SC-002**: 100% of first uploads after a long idle period succeed without a cold-start delay.
- **SC-003**: At least 90% of usability testers can identify the upload area and locate the result without help.
- **SC-004**: The assistant styling matches the portfolio on desktop and mobile in 100% of tested viewports.
- **SC-005**: The backend processes at least 1,000 photo reviews per day on the free tier without quota errors.
- **SC-006**: No uploaded photos are retained by the application after the response is sent.

## Key Entities

- **PhotoUploadRequest**: The client payload containing a resized image, dimensions, and filename.
- **DetectedObject**: A subject detected in the photo, including label, confidence score, and bounding box.
- **SceneLabel**: A scene classification result, including label and confidence score.
- **GuidanceTip**: A photography suggestion with category, text, and reason.
- **PhotoGuidanceResult**: The complete response returned to the client, including summary, tips, subjects, scenes, and uncertainty flag.

## Assumptions

- The maintainer will create a free Cloudflare account and authenticate Wrangler after updating Node.js to v22+.
- The portfolio is a React app deployed to GitHub Pages with a known public origin.
- Visitors have modern browsers supporting HTML5 Canvas, Fetch, and ES modules.
- Cloudflare Workers AI remains available on the free tier with current limits.
- The maintainer is comfortable copying a React component and CSS file into the `myWebSite` repository.

## Dependencies

- Cloudflare Workers AI object detection model `@cf/facebook/detr-resnet-50`.
- Cloudflare Workers AI image classification model `@cf/microsoft/resnet-50`.
- Wrangler CLI for Worker deployment.
- React 18+ in the portfolio.

## Out of Scope

- User accounts, galleries, or persistent history.
- Abuse protection such as CAPTCHA or rate limiting.
- Real-time updates or WebSocket communication.
- Batch uploads or video analysis.
- Replacing GitHub Pages with another host.
