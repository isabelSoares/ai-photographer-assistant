# Data Model: Add AI Assistant Link

## Assistant Destination

Represents the separately deployed assistant location used by the portfolio.

### Fields

- `url`: Public absolute HTTPS URL embedded into the static production bundle.
- `environment`: `production` for the published portfolio destination; local/test values are not publishable.
- `publication_status`: `configured`, `verified`, or `invalid`.

### Validation Rules

- `url` is required for a production build.
- `url` must parse as an absolute URL with the `https:` protocol.
- `url` must not be localhost, a loopback/private development address, an example domain, a placeholder, or a GitHub repository URL.
- The URL may include a path, such as `/photo-review`.
- No credential, token, or private configuration may be included in the value.

### State Transitions

```text
configured -> verified
configured -> invalid
invalid -> configured
```

Only `verified` destinations may be used by the production Pages publication.

## Assistant Invitation

Represents the visitor-facing homepage call to action.

### Fields

- `label`: Descriptive text, for example `Try the AI Photographer Assistant`.
- `destination`: Reference to the verified Assistant Destination.
- `opens_in_new_context`: True for the separate assistant tab/window behavior.
- `accessible_name`: The link text must communicate purpose without relying on an icon or color.
- `visual_theme`: Existing light/dark portfolio theme styling.

### Validation Rules

- The invitation is a native link, not a button that depends on JavaScript.
- The link includes opener protection when opening a new context.
- The link remains visible and keyboard-focusable in both theme modes and on narrow screens.

## Navigation Interaction

Optional aggregate observation of a visitor selecting the invitation.

### Fields

- `interaction_name`: Stable name such as `ai_assistant_link_click`.
- `destination_environment`: Production only for published traffic.

### Privacy Rules

- Analytics are disabled by default for this feature.
- If enabled, the interaction contains no uploaded photo, assistant result, or sensitive user data.
- Navigation must not depend on analytics availability.
