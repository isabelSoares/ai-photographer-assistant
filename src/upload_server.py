from __future__ import annotations

import html
import json
import os
import threading
from email import policy
from email.parser import BytesParser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse

from .upload_service import (
    MAX_UPLOAD_BYTES,
    DEFAULT_MODEL_PATH,
    PhotoGuidanceResult,
    ReviewState,
    UploadValidationError,
    review_upload,
)


MAX_REQUEST_BYTES = MAX_UPLOAD_BYTES + 1024 * 1024
review_lock = threading.Lock()
DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = 8000
DEFAULT_REVISION = "development"


def safe_error(error: Exception) -> str:
    if isinstance(error, UploadValidationError):
        return str(error)
    return "The photo could not be analyzed. Try again or choose another photo."


def result_payload(result: PhotoGuidanceResult) -> dict:
    return {
        "state": result.state.value,
        "upload_name": result.upload_name,
        "summary": result.summary,
        "subjects": result.subjects or [],
        "scenes": result.scenes or [],
        "tips": result.tips or [],
        "uncertain": result.uncertain,
        "notice": result.notice,
        "error_message": result.error_message,
    }


def _parse_photo(content_type: str, body: bytes) -> tuple[str, bytes]:
    message = BytesParser(policy=policy.default).parsebytes(
        f"Content-Type: {content_type}\r\nMIME-Version: 1.0\r\n\r\n".encode() + body
    )
    for part in message.walk():
        if part.get_content_disposition() != "form-data" or part.get_param("name", header="content-disposition") != "photo":
            continue
        return part.get_filename() or "selected photo", part.get_payload(decode=True) or b""
    raise UploadValidationError("Choose one photo to review.")


def render_page(result: PhotoGuidanceResult | None = None, error: str | None = None) -> str:
    payload = result_payload(result) if result else {"state": ReviewState.IDLE.value}
    upload_name = html.escape(str(payload.get("upload_name") or ""))
    summary = html.escape(str(payload.get("summary") or ""))
    message = html.escape(error or str(payload.get("error_message") or ""))
    tips = payload.get("tips") or []
    tip_markup = "".join(
        f'<li><strong>{html.escape(str(tip.get("category", "tip")))}</strong>: '
        f'{html.escape(str(tip.get("text", "")))} '
        f'<small>{html.escape(str(tip.get("reason", "")))}</small></li>'
        for tip in tips
    )
    uncertainty = "<p role=\"status\">Some suggestions are tentative because parts of the analysis are uncertain.</p>" if payload.get("uncertain") else ""
    state = html.escape(str(payload.get("state", ReviewState.IDLE.value)))
    error_markup = f'<section class="error" role="alert"><p>{message}</p><button type="button" onclick="resetReview()">Try again</button> <button type="button" onclick="resetReview()">Choose another photo</button></section>' if message else ""
    result_markup = f'<section class="result"><p class="eyebrow">Review for {upload_name}</p><h2>{summary}</h2>{uncertainty}<ul>{tip_markup}</ul><button type="button" onclick="resetReview()">Review another photo</button></section>' if state == ReviewState.COMPLETED.value else ""
    return f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Photo guidance</title>
<style>body{{font-family:system-ui,sans-serif;background:#f5f1ea;color:#27221d;margin:0}}main{{max-width:720px;margin:0 auto;padding:clamp(1.5rem,5vw,4rem)}}.card{{background:#fffaf3;border:1px solid #d9cdbd;border-radius:18px;padding:clamp(1rem,4vw,2rem);box-shadow:0 10px 30px #38271912}}h1{{font-size:clamp(2rem,8vw,4rem);margin:.2rem 0 1rem}}h2{{font-size:1.35rem;line-height:1.4}}.drop{{display:grid;gap:1rem;border:2px dashed #b78154;border-radius:14px;padding:1.5rem;margin:1.5rem 0}}button{{border:0;border-radius:999px;background:#b95f3b;color:#fff;padding:.75rem 1.1rem;font:inherit;cursor:pointer}}button:disabled{{opacity:.5;cursor:wait}}.error{{background:#fff0ed;border-left:4px solid #b43d32;padding:1rem;margin-top:1rem}}small{{display:block;color:#65584d;margin-top:.35rem}}li{{margin:.8rem 0;line-height:1.5}}.eyebrow{{text-transform:uppercase;letter-spacing:.08em;font-size:.75rem;color:#8a563c}}</style></head>
<body><main><p class="eyebrow">AI photographer assistant</p><h1>Make your next frame stronger.</h1><p>Upload one photo and get practical suggestions for future photographs.</p><section class="card"><form id="review-form" action="/review" method="post" enctype="multipart/form-data"><label class="drop" for="photo"><strong>Choose a photo</strong><span>JPG, PNG, WEBP, BMP, TIFF, or HEIC. Maximum 10 MiB.</span><input id="photo" name="photo" type="file" accept=".jpg,.jpeg,.png,.webp,.bmp,.tiff,.heic,.heif,image/*" required onchange="showSelection()"></label><p id="selection" aria-live="polite">No photo selected.</p><button id="submit" type="submit" disabled>Review photo</button><p id="progress" role="status" hidden>Reviewing your photo...</p></form>{error_markup}{result_markup}</section></main>
<script>const form=document.getElementById('review-form'),file=document.getElementById('photo'),selection=document.getElementById('selection'),submit=document.getElementById('submit'),progress=document.getElementById('progress');function showSelection(){{selection.textContent=file.files.length?file.files[0].name:'No photo selected.';submit.disabled=!file.files.length}}function resetReview(){{window.location='/'}}form.addEventListener('submit',()=>{{submit.disabled=true;progress.hidden=false;window.setTimeout(()=>{{progress.textContent='This is taking longer than expected. You can try again or choose another photo.'}},30000)}});</script></body></html>"""


class UploadHandler(BaseHTTPRequestHandler):
    def _send_html(self, body: str, status: int = 200) -> None:
        encoded = body.encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(encoded)))
        self.end_headers()
        self.wfile.write(encoded)

    def _send_json(self, payload: dict, status: int = 200) -> None:
        encoded = json.dumps(payload).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(encoded)))
        self.end_headers()
        self.wfile.write(encoded)

    def _health_response(self) -> tuple[dict, int]:
        model_path: Path = self.server.model_path  # type: ignore[attr-defined]
        revision: str = self.server.release_revision  # type: ignore[attr-defined]
        if model_path.is_file():
            return {"status": "healthy", "revision": revision}, 200
        return {"status": "unhealthy", "revision": revision}, 503

    def do_GET(self) -> None:
        path = urlparse(self.path).path
        if path == "/healthz":
            payload, status = self._health_response()
            self._send_json(payload, status)
            return
        if path != "/":
            self._send_html(render_page(error="That page was not found."), 404)
            return
        self._send_html(render_page())

    def do_POST(self) -> None:
        if urlparse(self.path).path != "/review":
            self._send_html(render_page(error="That page was not found."), 404)
            return
        try:
            length = int(self.headers.get("Content-Length", "0"))
            if length > MAX_REQUEST_BYTES:
                raise UploadValidationError("This upload request is too large.")
            content_type = self.headers.get("Content-Type", "")
            if not content_type.startswith("multipart/form-data"):
                raise UploadValidationError("Submit one photo using the upload form.")
            filename, content = _parse_photo(content_type, self.rfile.read(length))
            if not review_lock.acquire(blocking=False):
                raise UploadValidationError("A photo is already being reviewed. Wait for it to finish.")
            try:
                result = review_upload(filename, content)
            finally:
                review_lock.release()
            self._send_html(render_page(result=result), 500 if result.state == ReviewState.ERROR else 200)
        except (ValueError, UploadValidationError) as error:
            self._send_html(render_page(error=safe_error(error)), 400)
        except Exception:
            self._send_html(render_page(error=safe_error(RuntimeError())), 500)

    def log_message(self, format: str, *args) -> None:
        return


def create_server(
    host: str | None = None,
    port: int | None = None,
    revision: str | None = None,
    model_path: Path | str | None = None,
) -> ThreadingHTTPServer:
    resolved_host = host if host is not None else os.environ.get("HOST", DEFAULT_HOST)
    resolved_port = port if port is not None else int(os.environ.get("PORT", str(DEFAULT_PORT)))
    server = ThreadingHTTPServer((resolved_host, resolved_port), UploadHandler)
    server.release_revision = revision or os.environ.get("APP_REVISION") or os.environ.get("GITHUB_SHA") or DEFAULT_REVISION
    server.model_path = Path(model_path or os.environ.get("MODEL_PATH", DEFAULT_MODEL_PATH))
    return server


def main() -> None:
    server = create_server()
    host, port = server.server_address
    print(f"Photo guidance available at http://{host}:{port}/")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
