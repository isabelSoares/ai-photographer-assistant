# Quickstart: Add AI Assistant Link

This guide validates the link in the sibling static portfolio repository and its GitHub Pages publication boundary.

## Prerequisites

- Node.js 24 and npm.
- A checkout of `/Users/isabelsoares/Repos/myWebSite`.
- A public HTTPS URL for the separately deployed AI Photographer Assistant.
- The website repository variable `AI_ASSISTANT_URL` configured before production publication.

## Local Validation

Run from `/Users/isabelsoares/Repos/myWebSite/ts-app`:

```bash
npm ci
REACT_APP_AI_ASSISTANT_URL=https://ai-photographer-assistant.onrender.com npm run validate:assistant-url
npm test -- --watchAll=false
REACT_APP_AI_ASSISTANT_URL=https://ai-photographer-assistant.onrender.com npm run build
```

Expected outcomes:

- URL validation accepts the public HTTPS assistant URL.
- The homepage test finds a link named for the AI Photographer Assistant and verifies its external destination and new-tab safety attributes.
- The production build completes successfully.

## Negative Configuration Checks

The URL validation command must fail for each of these values:

```text
<missing>
https://your-ai-assistant.onrender.com
http://localhost:8000
https://github.com/isabelSoares/ai-photographer-assistant
https://example.com
```

The error must identify the invalid destination without printing unrelated environment variables.

## Browser Validation

1. Start the portfolio locally with the configured assistant URL.
2. Open the homepage at desktop width and verify the invitation is visible in the hero action group.
3. Tab to the invitation and verify a visible focus indicator and descriptive accessible name.
4. Select it and verify the assistant opens in a new tab while the portfolio remains in the original tab.
5. Repeat at a narrow mobile viewport and verify no horizontal overflow.
6. Switch between light and dark modes and verify readable contrast.
7. Temporarily use an unavailable assistant URL and verify the portfolio still loads and remains usable.

## GitHub Pages Validation

1. Set the website repository variable `AI_ASSISTANT_URL` to the verified public HTTPS assistant URL.
2. Open a pull request and confirm tests, URL validation, and the production build pass.
3. Confirm a placeholder or repository URL fails validation before merge/publication.
4. Merge the passing change to `main`.
5. Open `https://isabelsoares.github.io/myWebSite/` and select the invitation.
6. Confirm the destination is the deployed assistant URL, not the GitHub repository.

## Validation Record

Validated locally on 2026-10-06 against `https://ai-photographer-assistant.onrender.com`:

- `npm ci`: completed successfully; npm reported existing dependency deprecation and audit warnings.
- `npm run validate:assistant-url`: passed.
- `npm run test:assistant-url`: passed, including all invalid destination cases.
- `npm test -- --watchAll=false --runInBand`: passed with 2 tests.
- `npm run build`: completed successfully.
- Generated bundle contained the configured assistant URL and no placeholder or repository destination.
