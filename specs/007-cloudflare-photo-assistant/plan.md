# Implementation Plan: Cloudflare Photo Assistant

**Branch**: `007-cloudflare-photo-assistant` | **Date**: 2026-10-09 | **Spec**: [specs/007-cloudflare-photo-assistant/spec.md](./spec.md)

**Input**: Feature specification from `/specs/007-cloudflare-photo-assistant/spec.md`

## Summary

Build a no-sleep, free-tier photo assistant for the existing portfolio. The solution is a Cloudflare Worker backend that uses Workers AI for object detection and scene classification, plus a drop-in React component that the maintainer can embed in the React portfolio on GitHub Pages. The self-hosted YOLO pipeline is replaced by managed AI inference, removing Render Free's CPU and sleeping limitations.

## Technical Context

**Language/Version**: TypeScript (Worker), JavaScript/React 18+ (component), Node.js v22+ for Wrangler.

**Primary Dependencies**: Wrangler, Cloudflare Workers AI binding, React.

**Storage**: None. Uploaded images and results are ephemeral.

**Testing**: Manual quickstart validation; no automated test suite required for v1.

**Target Platform**: Cloudflare Workers edge runtime; portfolio static site on GitHub Pages.

**Project Type**: Web service (Worker) + reusable frontend component.

**Performance Goals**: Backend response under 10 seconds; no cold-start delay.

**Constraints**: Cloudflare Workers Free CPU limit of 10 ms per invocation; 10,000 AI neurons/day; 100,000 requests/day.

**Scale/Scope**: Small portfolio traffic; thousands of free daily photo reviews.

## Constitution Check

The project constitution is a placeholder, so no gates apply. The design is intentionally simple and matches the project's existing preference for small, self-contained features.

## Project Structure

### Documentation (this feature)

```text
specs/007-cloudflare-photo-assistant/
├── plan.md              # This file
├── research.md          # Decisions and alternatives
├── data-model.md        # Entities and validation rules
├── quickstart.md        # End-to-end validation steps
├── contracts/           # API contract
└── tasks.md             # Implementation task list
```

### Source Code (repository root)

```text
worker/
├── src/
│   └── index.ts         # Cloudflare Worker request handler and AI calls
├── package.json         # Wrangler and TypeScript dependencies
├── tsconfig.json        # TypeScript configuration
└── wrangler.toml        # Worker name, route, AI binding, CORS origin

web-component/
├── PhotoAssistant.jsx   # React upload + result component
└── photo-assistant.css  # Default theme using CSS variables

docs/
└── integration.md       # How to add the component to myWebSite
```

**Structure Decision**: A separate `worker/` directory for the backend and a `web-component/` directory for the reusable React component keeps the assistant decoupled from the existing Python source while remaining in the same repository for versioning.

## Complexity Tracking

No complexity violations. The feature intentionally uses managed AI to avoid hosting a heavy model.
