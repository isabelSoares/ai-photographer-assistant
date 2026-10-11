# Integrating the AI Photo Assistant into Your Portfolio

This guide explains how to add the `PhotoAssistant` React component to your `myWebSite` portfolio and deploy the Cloudflare Worker backend.

## What you need

- A free Cloudflare account.
- Node.js **v22.0.0 or newer** installed locally.
- Your portfolio repository (`myWebSite`) checked out on your machine.

## 1. Update Node.js (if needed)

Wrangler requires Node.js v22+. Check your version:

```bash
node -v
```

If it shows a version lower than v22, update with nvm:

```bash
# Install nvm if you don't have it
curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.40.0/install.sh | bash
# Restart your terminal, then:
nvm install 22
nvm use 22
nvm alias default 22
node -v
```

Then install Wrangler and log in:

```bash
npm install -g wrangler
wrangler login
```

## 2. Deploy the Cloudflare Worker

From this repository:

```bash
cd worker
npm install
wrangler deploy
```

After deployment, Wrangler prints your Worker URL, for example:

```text
https://ai-photo-assistant.<your-subdomain>.workers.dev
```

### Configure the allowed origin

Edit `worker/wrangler.toml` and set `PORTFOLIO_ORIGIN` to your GitHub Pages URL:

```toml
[vars]
PORTFOLIO_ORIGIN = "https://isabelsoares.github.io"
```

Then redeploy:

```bash
wrangler deploy
```

## 3. Copy the component into myWebSite

Copy the two files from this repo into your portfolio:

```bash
cp web-component/PhotoAssistant.tsx /path/to/myWebSite/src/components/
cp web-component/photo-assistant.scss /path/to/myWebSite/src/styles/
```

## 4. Import and use the component

In any React page (for example `src/pages/Assistant.jsx`):

```jsx
import PhotoAssistant from "../components/PhotoAssistant";
import "../styles/photo-assistant.scss";

export default function AssistantPage() {
  return (
    <PhotoAssistant
      workerUrl="https://ai-photo-assistant.<your-subdomain>.workers.dev/"
    />
  );
}
```

Replace the `workerUrl` with the URL from step 2.

## 5. Customize the design

The component uses CSS variables at the top of `photo-assistant.scss`. Change them to match your portfolio. If your React setup does not already compile SCSS, install the `sass` package:

```bash
npm install -D sass
```

```css
:root {
  --pa-bg: #f5f1ea;
  --pa-card-bg: #fffaf3;
  --pa-card-border: #d9cdbd;
  --pa-text: #27221d;
  --pa-muted: #65584d;
  --pa-accent: #b95f3b;
  --pa-accent-hover: #a34f30;
  --pa-error-bg: #fff0ed;
  --pa-error-border: #b43d32;
  --pa-error-text: #b43d32;
  --pa-radius: 18px;
  --pa-spacing: 1rem;
  --pa-font: system-ui, sans-serif;
}
```

## 6. Deploy your portfolio

Commit the new files and deploy to GitHub Pages as usual:

```bash
cd /path/to/myWebSite
git add .
git commit -m "Add AI photographer assistant"
git push
```

## 7. Test the end-to-end flow

1. Open the published portfolio page that contains the assistant.
2. Upload a JPG, PNG, or WEBP photo.
3. Wait a few seconds for the analysis.
4. Verify that a summary and at least one tip appear.
5. Test error handling by uploading a non-image file.
6. Resize the browser to a mobile width and confirm the layout is still usable.

## Troubleshooting

### CORS errors in the browser

Make sure `PORTFOLIO_ORIGIN` in `wrangler.toml` exactly matches the URL shown in the browser address bar, including `https://` and any path. After changing it, run `wrangler deploy` again.

### Worker responds with "Image is too large"

The Worker rejects images larger than ~1 MB after decoding. The component resizes photos to a max of 1024 px and compresses them as JPEG. If a file is still too large, lower the `maxDimension` or `quality` props:

```jsx
<PhotoAssistant workerUrl="..." maxDimension={768} quality={0.75} />
```

### Daily quota errors

Cloudflare Workers AI free tier includes 10,000 neurons per day. Object detection + classification uses roughly 1 neuron per photo, so the limit is thousands of photos per day. If you hit the limit, either wait until midnight UTC or upgrade to Cloudflare Workers Paid.

## Free-tier limits reminder

- **Workers requests**: 100,000/day.
- **Workers AI neurons**: 10,000/day.
- **Worker CPU time**: 10 ms per invocation (kept low because image resize happens in the browser).

No uploaded photos are stored by the Worker.
