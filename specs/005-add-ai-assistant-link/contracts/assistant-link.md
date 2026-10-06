# Assistant Link Contract

This contract defines the public handoff from the GitHub Pages portfolio to the separately deployed AI Photographer Assistant.

## Configuration

- The production build receives `AI_ASSISTANT_URL` from the website repository's deployment configuration or public repository variable.
- The build maps that value to the CRA public variable `REACT_APP_AI_ASSISTANT_URL`.
- The value is public client configuration after bundling and MUST NOT contain credentials or tokens.

## Destination Requirements

The production destination MUST:

- Be an absolute URL.
- Use `https:`.
- Refer to the separately deployed assistant application.
- Be publicly intended for portfolio visitors.
- Not be a GitHub repository URL, localhost, loopback/private address, example domain, or placeholder.

Valid examples:

```text
https://ai-photographer-assistant.onrender.com/
https://ai-photographer-assistant.onrender.com/photo-review
```

Invalid examples:

```text
https://github.com/isabelSoares/ai-photographer-assistant
http://localhost:8000
https://your-ai-assistant.onrender.com
```

## Link Behavior

- The portfolio renders a native anchor with visible text equivalent to `Try the AI Photographer Assistant`.
- The anchor uses `target="_blank"` and `rel="noopener noreferrer"`.
- The text or accessible context communicates that the assistant opens separately.
- The link works when JavaScript is disabled.
- The link does not make a request to the assistant while the portfolio loads.

## Release Behavior

- Production validation rejects an invalid or missing destination before the Pages artifact is published.
- The generated bundle contains the verified HTTPS destination and no placeholder destination.
- The website remains independently usable if the assistant is unavailable after navigation.
