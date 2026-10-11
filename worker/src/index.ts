import type { Ai } from "@cloudflare/workers-types";
import type { DetectedObject, PhotoGuidanceResult, PhotoUploadRequest, SceneLabel } from "./types";
import { generateGuidance } from "./tips";

export interface Env {
  AI: Ai;
  PORTFOLIO_ORIGIN: string;
}

export class ClientError extends Error {}

function corsHeaders(origin: string): Record<string, string> {
  return {
    "Access-Control-Allow-Origin": origin,
    "Access-Control-Allow-Methods": "POST, OPTIONS",
    "Access-Control-Allow-Headers": "Content-Type",
  };
}

function jsonResponse(body: unknown, status: number, origin: string): Response {
  return new Response(JSON.stringify(body), {
    status,
    headers: {
      "Content-Type": "application/json; charset=utf-8",
      ...corsHeaders(origin),
    },
  });
}

function validateRequest(body: unknown): PhotoUploadRequest {
  if (typeof body !== "object" || body === null) {
    throw new ClientError("Invalid request body.");
  }
  const req = body as Record<string, unknown>;
  if (typeof req.image !== "string" || !req.image.startsWith("data:image/")) {
    throw new ClientError("Invalid image format. Please upload a JPG, PNG, or WEBP photo.");
  }
  if (typeof req.width !== "number" || !Number.isInteger(req.width) || req.width <= 0 || req.width > 1024) {
    throw new ClientError("Invalid image width.");
  }
  if (typeof req.height !== "number" || !Number.isInteger(req.height) || req.height <= 0 || req.height > 1024) {
    throw new ClientError("Invalid image height.");
  }
  if (typeof req.filename !== "string" || req.filename.length > 255) {
    throw new ClientError("Invalid filename.");
  }
  return {
    image: req.image,
    width: req.width,
    height: req.height,
    filename: req.filename,
  };
}

function dataUrlToBytes(dataUrl: string): Uint8Array {
  const match = dataUrl.match(/^data:image\/(\w+);base64,(.+)$/);
  if (!match) {
    throw new ClientError("Invalid image data URL.");
  }
  const format = match[1].toLowerCase();
  if (!["jpeg", "jpg", "png", "webp"].includes(format)) {
    throw new ClientError("Unsupported image format. Please upload JPG, PNG, or WEBP.");
  }
  const base64 = match[2];
  try {
    const binary = atob(base64);
    const bytes = new Uint8Array(binary.length);
    for (let i = 0; i < binary.length; i++) {
      bytes[i] = binary.charCodeAt(i);
    }
    return bytes;
  } catch {
    throw new ClientError("Could not decode image data.");
  }
}

async function runObjectDetection(imageBytes: Uint8Array, ai: Ai): Promise<DetectedObject[]> {
  const response = (await ai.run("@cf/facebook/detr-resnet-50", {
    image: Array.from(imageBytes),
  })) as { results?: DetectedObject[] } | DetectedObject[];
  const results = Array.isArray(response) ? response : response.results ?? [];
  return results
    .filter((r) => r.score >= 0.5)
    .sort((a, b) => b.score - a.score);
}

async function runClassification(imageBytes: Uint8Array, ai: Ai): Promise<SceneLabel[]> {
  const response = (await ai.run("@cf/microsoft/resnet-50", {
    image: Array.from(imageBytes),
  })) as { results?: SceneLabel[] } | SceneLabel[];
  const results = Array.isArray(response) ? response : response.results ?? [];
  return results
    .filter((r) => r.score >= 0.2)
    .sort((a, b) => b.score - a.score)
    .slice(0, 3);
}

export default {
  async fetch(request: Request, env: Env): Promise<Response> {
    const origin = env.PORTFOLIO_ORIGIN || "*";

    if (request.method === "OPTIONS") {
      return new Response(null, { status: 204, headers: corsHeaders(origin) });
    }

    if (request.method !== "POST") {
      return jsonResponse({ error: "Method not allowed." }, 405, origin);
    }

    try {
      const body = (await request.json()) as unknown;
      const req = validateRequest(body);
      const imageBytes = dataUrlToBytes(req.image);

      if (imageBytes.byteLength > 1_000_000) {
        throw new ClientError("Image is too large. Please choose a smaller photo.");
      }

      const [detections, scenes] = await Promise.all([
        runObjectDetection(imageBytes, env.AI),
        runClassification(imageBytes, env.AI),
      ]);

      const result: PhotoGuidanceResult = generateGuidance(
        detections,
        scenes,
        req.width,
        req.height,
        req.filename
      );

      return jsonResponse(result, 200, origin);
    } catch (err) {
      if (err instanceof ClientError) {
        return jsonResponse({ error: err.message }, 400, origin);
      }
      console.error(err);
      return jsonResponse(
        { error: "The photo could not be analyzed. Please try again or choose another photo." },
        500,
        origin
      );
    }
  },
} satisfies ExportedHandler<Env>;
