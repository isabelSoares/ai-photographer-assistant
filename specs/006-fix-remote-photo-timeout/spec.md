# Feature Specification: Fix Remote Photo Upload Timeouts and 502 Errors

**Short name**: `fix-remote-photo-timeout`

**Feature Branch**: `006-fix-remote-photo-timeout`

**Feature Directory**: `specs/006-fix-remote-photo-timeout`

**Created**: 2026-10-07

**Status**: Draft

**Input**: User description: "I put this site available remotely. It takes so much time for a photo, I uploaded another photo and then I have 502 Bad Gateway."

## Decisions from Clarifications

- **Q1**: First status update must be visible within **5 seconds**.
- **Q2**: Photos are analyzed **one at a time**; additional uploads are **queued** in submission order.
- **Q3**: Results appear **automatically on the same page** as analysis progresses.

## Problem Statement

When the photo-guidance site is accessed over the internet, uploading a photo is unacceptably slow, and attempting to upload a second photo while the first is still being processed produces a `502 Bad Gateway` error. These symptoms indicate that the current request handling keeps the network connection open for the entire duration of photo analysis, which exceeds typical remote reverse-proxy timeout limits and leaves users with a broken, confusing experience.

## Goals

- Make the remote upload experience responsive enough that users do not encounter gateway errors.
- Allow a user to submit a new photo without being blocked by a prior in-progress review.
- Provide clear, honest status about analysis progress so users know whether to wait or retry.
- Ensure that a slow or failed review does not crash the upload service or prevent future uploads.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Upload a Photo Remotely Without Gateway Errors (Priority: P1)

As a photographer using the site from a remote network, I want to upload a photo and receive guidance without seeing a `502 Bad Gateway` error, so that the remote site feels reliable.

**Why this priority**: The 502 error makes the feature unusable remotely and is the primary complaint.

**Independent Test**: A tester on a remote network can upload one supported photo and verify that the server accepts the request and returns a stable response.

**Acceptance Scenarios**:

1. **Given** the user is on a remote network, **When** they upload one supported photo, **Then** the server accepts the request and returns a response before any gateway timeout.
2. **Given** a photo is being analyzed, **When** the analysis takes longer than a few seconds, **Then** the user sees a progress indicator and the connection remains stable.
3. **Given** analysis completes, **When** the result is ready, **Then** the user sees the guidance result without needing to refresh or re-upload.

---

### User Story 2 - Upload a Second Photo While Another Is Processing (Priority: P1)

As a photographer, I want to upload another photo even if the previous one is still being analyzed, so that I am not stuck waiting for one slow review.

**Why this priority**: The current behavior causes a 502 when a second upload is attempted; removing this blocker is essential for a usable multi-photo workflow.

**Independent Test**: A tester can submit one photo, immediately submit a second supported photo, and verify that both are accepted and each receives its own result.

**Acceptance Scenarios**:

1. **Given** one photo is already being analyzed, **When** the user submits a second photo, **Then** the site accepts the second upload and places it in a queue rather than returning a gateway error.
2. **Given** multiple photos are queued, **When** each analysis finishes, **Then** the user can access each corresponding result without results being mixed up.
3. **Given** the server is busy, **When** the user tries to upload, **Then** they receive a clear message about queue position or expected wait time instead of a generic error.

---

### User Story 3 - Recover from Slow or Failed Analysis (Priority: P2)

As a photographer, I want understandable feedback when analysis is slow or fails, so that I know whether to wait, retry, or choose a different photo.

**Independent Test**: A tester can simulate a slow or failed analysis and verify that the page continues to communicate status and offers recovery actions.

**Acceptance Scenarios**:

1. **Given** analysis is taking longer than expected, **When** the user waits, **Then** the page continues to show a helpful status and does not silently time out.
2. **Given** analysis fails, **When** the failure occurs, **Then** the user sees a plain-language error and a clear retry/replace action.
3. **Given** the user refreshes the page during processing, **When** the page reloads, **Then** they can see the status of their ongoing or most recent review.

### Edge Cases

- The user submits a second photo before the first has finished analyzing.
- The user submits multiple photos in rapid succession while earlier ones are still queued.
- The user refreshes or navigates away while analysis is in progress.
- The reverse proxy or gateway has a shorter timeout than the analysis duration.
- The remote server is under heavy load and cannot analyze photos immediately.
- A prior analysis fails but the user immediately tries another upload.
- The user submits the same photo more than once in overlapping requests.
- The queue grows longer than the user is willing to wait; the user needs clear wait-time guidance.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The feature MUST accept a photo upload from a remote user and return an initial response within 5 seconds to avoid gateway timeouts.
- **FR-002**: The feature MUST allow a second upload to begin while a prior upload is still being analyzed, without returning a `502 Bad Gateway` error.
- **FR-003**: When the server is already analyzing a photo, newly accepted uploads MUST be placed in a queue and analyzed one at a time in submission order.
- **FR-004**: The feature MUST clearly distinguish between upload accepted, queued, analysis in progress, completed result, and error states.
- **FR-005**: The feature MUST associate every result with the correct uploaded photo, even when multiple photos are submitted in overlapping sessions.
- **FR-006**: The feature MUST display the user's queue position or an estimated wait time when an upload is not analyzed immediately.
- **FR-007**: The feature MUST provide a plain-language message when analysis is queued, slow, or temporarily unavailable.
- **FR-008**: The feature MUST allow the user to retry or replace a photo after any failure without restarting the entire experience.
- **FR-009**: The feature MUST continue to enforce existing validation rules for file format, size, and image integrity.
- **FR-010**: The feature MUST not retain uploaded photos longer than necessary to produce the requested guidance.

### Non-Functional Requirements

- **NFR-001**: The upload endpoint MUST respond to the client within 5 seconds under normal remote network conditions.
- **NFR-002**: The system MUST handle at least 2 concurrent photo submissions without gateway errors or data mix-ups.
- **NFR-003**: Analysis MUST continue in the background even if the user navigates away or refreshes the page.
- **NFR-004**: Only one analysis job MUST run at a time; additional jobs MUST wait in a first-in-first-out queue.
- **NFR-005**: The feature MUST remain compatible with the existing supported image formats and 10 MiB upload limit.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: 95% of remote uploads receive a non-gateway-error response within 5 seconds.
- **SC-002**: No more than 1% of second-upload attempts result in a `502 Bad Gateway` error during normal operation.
- **SC-003**: Users can submit a new photo while another is processing, and each result is correctly matched to its photo.
- **SC-004**: 90% of users can clearly identify whether their upload is queued, in progress, completed, or failed.
- **SC-005**: Analysis of a single 10 MiB photo completes within 60 seconds under normal remote server conditions.
- **SC-006**: When a photo is queued, the user sees their queue position or an estimated wait time within 5 seconds of submission.
- **SC-007**: Failed or slow analyses do not prevent subsequent uploads from being accepted.

## Key Entities

- **Remote Photo Upload**: A photo submitted by a user over the internet, including file identity, format, size, and submission timestamp.
- **Analysis Job**: The background work required to analyze one uploaded photo and produce guidance.
- **Review Queue**: The ordered list of accepted uploads waiting to be analyzed one at a time.
- **Review Status**: The current state of a user's upload (accepted, queued, processing, completed, failed).
- **Guidance Result**: The completed response associated with one specific uploaded photo.

## Assumptions

- A reverse proxy or gateway sits between remote users and the upload service and has a finite request timeout.
- The analysis pipeline is correct but may be slow on the remote host's resources.
- Users may have a stable but higher-latency connection than local development.
- Existing validation, privacy, and retention rules from the photo-upload-guidance feature remain in effect.
- The remote server is sized to run one analysis job at a time; additional capacity is not required for this feature.
- Auto-updates on the same page are acceptable for v1; a separate results page or email notification is out of scope.
- Completed and failed job results are retained in memory for up to 10 minutes so a refresh can recover the latest status, but no permanent gallery or history is created.
- The reverse-proxy timeout is assumed to be at least 5 seconds; if it is shorter, the initial response must still fit within the proxy limit.

## Dependencies

- Existing photo analysis pipeline (detection, image analysis, recommendations).
- Existing upload validation and normalization logic.
- Remote deployment infrastructure (host, reverse proxy, network).

## Out of Scope

- Redesigning the user interface beyond status and error messaging.
- Changing the object-detection model or improving analysis accuracy.
- Adding user accounts, galleries, or persistent history.
- Batch uploads of multiple photos in a single request.
- Push notifications, email results, or native mobile apps.
