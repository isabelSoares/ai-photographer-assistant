import { useState, useRef, useCallback, ChangeEvent, FormEvent } from "react";

export interface DetectedObject {
  label: string;
  score: number;
  box: {
    xmin: number;
    ymin: number;
    xmax: number;
    ymax: number;
  };
}

export interface SceneLabel {
  label: string;
  score: number;
}

export interface GuidanceTip {
  category: string;
  text: string;
  reason?: string;
}

export interface PhotoGuidanceResult {
  summary: string;
  subjects: DetectedObject[];
  scenes: SceneLabel[];
  tips: GuidanceTip[];
  uncertain: boolean;
  notice: string | null;
  error_message: string | null;
}

export interface PhotoAssistantProps {
  /** URL of the Cloudflare Worker backend. */
  workerUrl: string;
  /** Max width/height for the resized image. */
  maxDimension?: number;
  /** JPEG compression quality (0-1). */
  quality?: number;
  /** Extra CSS class for the root element. */
  className?: string;
}

const SUPPORTED_TYPES = ["image/jpeg", "image/png", "image/webp"] as const;
const MAX_FILE_SIZE = 10 * 1024 * 1024; // 10 MiB
const DEFAULT_MAX_DIMENSION = 1024;
const DEFAULT_QUALITY = 0.85;

interface ResizeResult {
  dataUrl: string;
  width: number;
  height: number;
}

/**
 * Resize an image in the browser using an off-screen canvas.
 * Returns a JPEG data URL and the new dimensions.
 */
function resizeImage(
  dataUrl: string,
  maxDimension: number,
  quality: number
): Promise<ResizeResult> {
  return new Promise((resolve, reject) => {
    const img = new Image();
    img.onload = () => {
      let { width, height } = img;
      if (width > maxDimension || height > maxDimension) {
        if (width > height) {
          height = Math.round((height * maxDimension) / width);
          width = maxDimension;
        } else {
          width = Math.round((width * maxDimension) / height);
          height = maxDimension;
        }
      }
      const canvas = document.createElement("canvas");
      canvas.width = width;
      canvas.height = height;
      const ctx = canvas.getContext("2d");
      if (!ctx) {
        reject(new Error("Could not create canvas context."));
        return;
      }
      ctx.drawImage(img, 0, 0, width, height);
      const resized = canvas.toDataURL("image/jpeg", quality);
      resolve({ dataUrl: resized, width, height });
    };
    img.onerror = () => reject(new Error("Could not read the selected photo."));
    img.src = dataUrl;
  });
}

export default function PhotoAssistant({
  workerUrl,
  maxDimension = DEFAULT_MAX_DIMENSION,
  quality = DEFAULT_QUALITY,
  className = "",
}: PhotoAssistantProps) {
  const [file, setFile] = useState<File | null>(null);
  const [preview, setPreview] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<PhotoGuidanceResult | null>(null);
  const [error, setError] = useState<string | null>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  const handleFileChange = useCallback((event: ChangeEvent<HTMLInputElement>) => {
    const selected = event.target.files?.[0];
    setResult(null);
    setError(null);
    setFile(null);
    setPreview(null);

    if (!selected) return;

    if (!SUPPORTED_TYPES.includes(selected.type as typeof SUPPORTED_TYPES[number])) {
      setError("Please upload a JPG, PNG, or WEBP photo.");
      return;
    }
    if (selected.size > MAX_FILE_SIZE) {
      setError("Photo must be smaller than 10 MB.");
      return;
    }

    const reader = new FileReader();
    reader.onload = () => {
      setFile(selected);
      setPreview(reader.result as string);
    };
    reader.onerror = () => setError("Could not read the selected photo.");
    reader.readAsDataURL(selected);
  }, []);

  const handleSubmit = useCallback(
    async (event: FormEvent<HTMLFormElement>) => {
      event.preventDefault();
      if (!file || !preview) return;

      setLoading(true);
      setError(null);
      setResult(null);

      try {
        const { dataUrl, width, height } = await resizeImage(preview, maxDimension, quality);

        const response = await fetch(workerUrl, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            image: dataUrl,
            width,
            height,
            filename: file.name,
          }),
        });

        const data = (await response.json().catch(() => ({}))) as PhotoGuidanceResult & { error?: string };

        if (!response.ok) {
          throw new Error(data.error || "The photo could not be analyzed. Please try again.");
        }

        setResult(data);
      } catch (err) {
        setError(err instanceof Error ? err.message : "Something went wrong. Please try again.");
      } finally {
        setLoading(false);
      }
    },
    [file, preview, maxDimension, quality, workerUrl]
  );

  const handleReset = useCallback(() => {
    setFile(null);
    setPreview(null);
    setResult(null);
    setError(null);
    if (inputRef.current) {
      inputRef.current.value = "";
    }
  }, []);

  return (
    <div className={`photo-assistant ${className}`}>
      <div className="photo-assistant__card">
        <h2 className="photo-assistant__title">AI Photographer Assistant</h2>
        <p className="photo-assistant__subtitle">
          Upload a photo and get practical suggestions for your next shot.
        </p>

        {!result && (
          <form onSubmit={handleSubmit} className="photo-assistant__form">
            <label className="photo-assistant__drop">
              <input
                ref={inputRef}
                type="file"
                accept=".jpg,.jpeg,.png,.webp,image/*"
                onChange={handleFileChange}
                disabled={loading}
              />
              <span className="photo-assistant__drop-text">
                {preview ? file?.name : "Click or drag a photo here"}
              </span>
              <span className="photo-assistant__drop-hint">
                JPG, PNG, or WEBP. Max 10 MB.
              </span>
            </label>

            {preview && (
              <img
                src={preview}
                alt="Selected preview"
                className="photo-assistant__preview"
              />
            )}

            {error && <div className="photo-assistant__error" role="alert">{error}</div>}

            <div className="photo-assistant__actions">
              <button
                type="submit"
                className="photo-assistant__button photo-assistant__button--primary"
                disabled={!preview || loading}
              >
                {loading ? "Analyzing..." : "Review photo"}
              </button>
            </div>
          </form>
        )}

        {loading && (
          <div className="photo-assistant__status" role="status">
            <span className="photo-assistant__spinner" aria-hidden="true" />
            Analyzing your photo...
          </div>
        )}

        {result && (
          <div className="photo-assistant__result">
            <p className="photo-assistant__eyebrow">Review</p>
            <h3 className="photo-assistant__summary">{result.summary}</h3>

            {result.uncertain && result.notice && (
              <p className="photo-assistant__notice">{result.notice}</p>
            )}

            {result.tips?.length > 0 && (
              <ul className="photo-assistant__tips">
                {result.tips.map((tip, index) => (
                  <li key={index} className="photo-assistant__tip">
                    <strong className="photo-assistant__tip-category">
                      {tip.category}
                    </strong>
                    <span className="photo-assistant__tip-text">{tip.text}</span>
                    {tip.reason && (
                      <small className="photo-assistant__tip-reason">
                        {tip.reason}
                      </small>
                    )}
                  </li>
                ))}
              </ul>
            )}

            {(result.subjects?.length > 0 || result.scenes?.length > 0) && (
              <div className="photo-assistant__tags">
                {result.subjects?.map((subject, index) => (
                  <span key={`s-${index}`} className="photo-assistant__tag">
                    {subject.label}
                  </span>
                ))}
                {result.scenes?.map((scene, index) => (
                  <span
                    key={`c-${index}`}
                    className="photo-assistant__tag photo-assistant__tag--scene"
                  >
                    {scene.label.replace(/_/g, " ")}
                  </span>
                ))}
              </div>
            )}

            <div className="photo-assistant__actions">
              <button
                type="button"
                className="photo-assistant__button photo-assistant__button--secondary"
                onClick={handleReset}
              >
                Review another photo
              </button>
            </div>
          </div>
        )}

        <p className="photo-assistant__privacy">
          Your photo is analyzed in real time and not stored.
        </p>
      </div>
    </div>
  );
}
