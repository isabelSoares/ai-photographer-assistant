# Research: Cloudflare Photo Assistant

**Date**: 2026-10-09

## Decision

Use a **Cloudflare Worker** with **Workers AI** for the backend and a **React component** embedded in the GitHub Pages portfolio.

## Rationale

- The existing Render Free deployment fails because it provides only 0.1 CPU and spins down after 15 minutes of inactivity.
- The user does not have a guaranteed Hugging Face account in good standing, so Hugging Face Spaces ZeroGPU is not a reliable path.
- Cloudflare Workers never sleep and the free tier is sufficient for object detection + image classification.
- Object detection (`@cf/facebook/detr-resnet-50`) and classification (`@cf/microsoft/resnet-50`) together cost roughly ~1 neuron per photo, allowing thousands of daily reviews on the free 10,000 neuron/day allowance.
- A custom React component lets the assistant match the portfolio design exactly, unlike a Streamlit or Gradio iframe.
- GitHub Pages remains the static host; the backend runs separately on Cloudflare.

## Alternatives considered

| Option | Why rejected |
|---|---|
| Hugging Face Spaces | Free Gradio/ZeroGPU Spaces require an account in good standing (verified email, >30 days), which the user cannot guarantee. |
| Streamlit Community Cloud | Apps sleep after 12 hours and the UI cannot match the portfolio exactly. |
| Vercel Python serverless functions | Cold starts and package size make YOLO hosting unreliable on the free tier. |
| Keep Render Free | 0.1 CPU is too slow for YOLO inference; this is the root cause of the missing suggestions. |
| Cloudflare Workers AI with a vision-language model for tips | Free neuron quota would be exhausted after only a few photos per day. Rule-based tips keep usage low. |

## Key constraints

- Cloudflare Workers Free allows 10 ms CPU time per invocation. Image resize must happen in the browser; the Worker only forwards bytes and runs a small rule engine.
- Workers Free allows 100,000 requests/day and 10,000 AI neurons/day.
- The portfolio origin must be whitelisted in the Worker CORS configuration.
- Uploaded images are not stored by the Worker, but Cloudflare's own processing terms apply while inference runs.

## Models chosen

- `@cf/facebook/detr-resnet-50` for object detection.
- `@cf/microsoft/resnet-50` for scene classification.

Both models are available on the Workers Free plan and priced low enough to stay within the free neuron allowance.
