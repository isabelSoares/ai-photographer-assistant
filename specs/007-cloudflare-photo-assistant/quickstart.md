# Quickstart: Cloudflare Photo Assistant

## Prerequisites

- Free Cloudflare account.
- Node.js v22+ installed and Wrangler authenticated (`wrangler login`).
- Portfolio repository `myWebSite` is a React app deployed to GitHub Pages.

## 1. Deploy the Worker

```bash
cd worker
npm install
wrangler deploy
```

Note the deployed Worker URL (e.g. `https://ai-photo-assistant.<your-subdomain>.workers.dev`).

## 2. Configure CORS origin

Edit `worker/wrangler.toml` and set `PORTFOLIO_ORIGIN` to your GitHub Pages URL, then redeploy:

```bash
wrangler deploy
```

## 3. Add the component to your portfolio

Copy the component files into `myWebSite`:

```bash
cp web-component/PhotoAssistant.jsx myWebSite/src/components/
cp web-component/photo-assistant.css myWebSite/src/styles/
```

Import and use it in a page:

```jsx
import PhotoAssistant from "../components/PhotoAssistant";
import "../styles/photo-assistant.css";

export default function AssistantPage() {
  return (
    <PhotoAssistant
      workerUrl="https://ai-photo-assistant.<your-subdomain>.workers.dev/"
    />
  );
}
```

## 4. Deploy the portfolio

```bash
cd myWebSite
npm run deploy   # or your usual GitHub Pages deploy command
```

## 5. Validate end-to-end

1. Open the published portfolio page containing the assistant.
2. Select a JPG, PNG, or WEBP photo under 10 MB.
3. Confirm the photo preview appears and the upload starts.
4. Wait for the result.
5. Verify you see:
   - A summary sentence.
   - At least one tip.
   - A list of detected subjects (if any) and scene labels (if any).
6. Test error handling by selecting a non-image file.
7. Resize the browser to mobile width and confirm the layout remains usable.

## 6. Check quota usage

In the Cloudflare dashboard, verify Workers AI neuron usage stays within the free 10,000 neurons/day allowance.
