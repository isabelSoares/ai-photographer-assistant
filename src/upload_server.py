from __future__ import annotations

import html
import json
import os
import re
import threading
from email import policy
from email.parser import BytesParser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

from .upload_jobs import (
    MAX_QUEUE_LENGTH,
    AnalysisWorker,
    CleanupWorker,
    JobNotFoundError,
    JobState,
    JobStore,
    QueueBusyError,
    ReviewQueue,
    create_job_from_upload,
    get_job_status,
)
from .upload_service import (
    MAX_UPLOAD_BYTES,
    DEFAULT_MODEL_PATH,
    PhotoGuidanceResult,
    ReviewState,
    UploadValidationError,
)


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


MAX_REQUEST_BYTES = MAX_UPLOAD_BYTES + 1024 * 1024
DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = 8000
DEFAULT_REVISION = "development"
POLL_INTERVAL_MS = 2000


def safe_error(error: Exception) -> str:
    if isinstance(error, UploadValidationError):
        return str(error)
    if isinstance(error, QueueBusyError):
        return str(error)
    return "The photo could not be analyzed. Try again or choose another photo."


def _parse_photo(content_type: str, body: bytes) -> tuple[str, bytes]:
    message = BytesParser(policy=policy.default).parsebytes(
        f"Content-Type: {content_type}\r\nMIME-Version: 1.0\r\n\r\n".encode() + body
    )
    for part in message.walk():
        if part.get_content_disposition() != "form-data" or part.get_param("name", header="content-disposition") != "photo":
            continue
        return part.get_filename() or "selected photo", part.get_payload(decode=True) or b""
    raise UploadValidationError("Choose one photo to review.")


def _status_message(state: str, queue_position: int | None, upload_name: str) -> str:
    if state == JobState.QUEUED.value and queue_position is not None:
        if queue_position == 1:
            return f"{upload_name} is next in line for review."
        return f"{upload_name} is number {queue_position} in line for review."
    if state == JobState.PROCESSING.value:
        return f"Reviewing {upload_name}..."
    if state == JobState.COMPLETED.value:
        return f"Review complete for {upload_name}."
    if state == JobState.FAILED.value:
        return f"Could not review {upload_name}."
    return f"{upload_name} has been accepted."


def render_page(job_state: str | None = None, upload_name: str | None = None, error: str | None = None) -> str:
    initial_status = html.escape(error or "")
    if not initial_status and upload_name and job_state:
        initial_status = html.escape(f"Resuming review for {upload_name}...")
    initial_state = html.escape(job_state or "idle")
    return f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Photo guidance</title>
<style>body{{font-family:system-ui,sans-serif;background:#f5f1ea;color:#27221d;margin:0}}main{{max-width:720px;margin:0 auto;padding:clamp(1.5rem,5vw,4rem)}}.card{{background:#fffaf3;border:1px solid #d9cdbd;border-radius:18px;padding:clamp(1rem,4vw,2rem);box-shadow:0 10px 30px #38271912}}h1{{font-size:clamp(2rem,8vw,4rem);margin:.2rem 0 1rem}}h2{{font-size:1.35rem;line-height:1.4}}.drop{{display:grid;gap:1rem;border:2px dashed #b78154;border-radius:14px;padding:1.5rem;margin:1.5rem 0}}button{{border:0;border-radius:999px;background:#b95f3b;color:#fff;padding:.75rem 1.1rem;font:inherit;cursor:pointer}}button:disabled{{opacity:.5;cursor:wait}}.error{{background:#fff0ed;border-left:4px solid #b43d32;padding:1rem;margin-top:1rem}}small{{display:block;color:#65584d;margin-top:.35rem}}li{{margin:.8rem 0;line-height:1.5}}.eyebrow{{text-transform:uppercase;letter-spacing:.08em;font-size:.75rem;color:#8a563c}}#status{{margin-top:1rem}}#result-area{{margin-top:1rem}}.completed-summary{{font-size:1.25rem;margin:.5rem 0}}.tip{{margin:.6rem 0}}</style></head>
<body><main><p class="eyebrow">AI photographer assistant</p><h1>Make your next frame stronger.</h1><p>Upload one photo and get practical suggestions for future photographs.</p><section class="card"><form id="review-form" action="/review" method="post" enctype="multipart/form-data"><label class="drop" for="photo"><strong>Choose a photo</strong><span>JPG, PNG, WEBP, BMP, TIFF, or HEIC. Maximum 10 MiB.</span><input id="photo" name="photo" type="file" accept=".jpg,.jpeg,.png,.webp,.bmp,.tiff,.heic,.heif,image/*" required onchange="showSelection()"></label><p id="selection" aria-live="polite">No photo selected.</p><button id="submit" type="submit" disabled>Review photo</button><p id="status" role="status" {'hidden' if not initial_status else ''}>{initial_status}</p></form><div id="result-area"></div></section></main>
<script>
const form=document.getElementById('review-form'),file=document.getElementById('photo'),selection=document.getElementById('selection'),submit=document.getElementById('submit'),statusEl=document.getElementById('status'),resultArea=document.getElementById('result-area');
let pollTimer=null, delayedTimer=null;
function showSelection(){{selection.textContent=file.files.length?file.files[0].name:'No photo selected.';submit.disabled=!file.files.length}}
function escapeHtml(text){{const div=document.createElement('div');div.textContent=text;return div.innerHTML;}}
function setStatus(text,visible=true){{statusEl.textContent=text;statusEl.hidden=!visible;}}
function clearResult(){{resultArea.innerHTML='';}}
function renderResult(data){{
  const result=data.result;
  if(!result)return;
  let markup='<section class="result"><p class="eyebrow">Review for '+escapeHtml(result.upload_name)+'</p><h2 class="completed-summary">'+escapeHtml(result.summary)+'</h2>';
  if(result.uncertain)markup+='<p role="status">Some suggestions are tentative because parts of the analysis are uncertain.</p>';
  if(result.tips&&result.tips.length){{markup+='<ul>'+result.tips.map(t=>'<li class="tip"><strong>'+escapeHtml(t.category||'tip')+'</strong>: '+escapeHtml(t.text)+' <small>'+escapeHtml(t.reason||'')+'</small></li>').join('')+'</ul>';}}
  markup+='<button type="button" onclick="resetReview()">Review another photo</button></section>';
  resultArea.innerHTML=markup;
}}
function renderError(message){{resultArea.innerHTML='<section class="error" role="alert"><p>'+escapeHtml(message)+'</p><button type="button" onclick="resetReview()">Try again</button> <button type="button" onclick="resetReview()">Choose another photo</button></section>';}}
function resetReview(){{clearTimeout(pollTimer);clearTimeout(delayedTimer);statusEl.hidden=true;resultArea.innerHTML='';form.reset();showSelection();history.replaceState(null,'','/');file.focus();}}
function startPolling(jobId){{
  const poll=async()=>{{
    try{{const res=await fetch('/status/'+encodeURIComponent(jobId));if(!res.ok&&res.status!==404)throw new Error('Status check failed');    const data=await res.json();setStatus(escapeHtml(data.message||'Checking status...'));if(data.state==='queued'||data.state==='processing'||data.state==='accepted'){{pollTimer=setTimeout(poll,{POLL_INTERVAL_MS});if(data.state==='processing'&&!delayedTimer)delayedTimer=setTimeout(()=>setStatus('This is taking longer than expected. You can try again or choose another photo.'),30000);}}else if(data.state==='completed'){{renderResult(data);}}else if(data.state==='failed'){{renderError(data.error_message||'The photo could not be analyzed.');}}}}
    catch(e){{renderError('Unable to check review status. You can try again.');}}
  }};
  poll();
}}
form.addEventListener('submit',async(e)=>{{
  e.preventDefault();if(!file.files.length)return;submit.disabled=true;setStatus('Uploading...');clearResult();
  const uploadName=file.files[0].name;
  try{{
    const body=new FormData(form);const res=await fetch('/review',{{method:'POST',body}});const data=await res.json();
    if(!res.ok){{renderError(data.error||'The upload could not be accepted.');submit.disabled=false;return;}}
    history.replaceState(null,'','/?job_id='+encodeURIComponent(data.job_id));
    startPolling(data.job_id);
  }}catch(err){{renderError('The upload could not be sent. Check your connection and try again.');submit.disabled=false;}}
}});
(function(){{
  const params=new URLSearchParams(window.location.search);const jobId=params.get('job_id');
  if(jobId){{submit.disabled=true;if(statusEl.textContent==='')setStatus('Resuming review...');startPolling(jobId);}}
  else{{showSelection();}}
}})();
</script></body></html>"""


class PhotoGuidanceServer(ThreadingHTTPServer):
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.job_store = JobStore()
        self.review_queue = ReviewQueue(max_length=MAX_QUEUE_LENGTH)
        self.analysis_worker = AnalysisWorker(self.review_queue, self.job_store)
        self.cleanup_worker = CleanupWorker(self.job_store)
        self.analysis_worker.start()
        self.cleanup_worker.start()

    def server_close(self) -> None:
        self.analysis_worker.stop(timeout=5)
        self.cleanup_worker.stop(timeout=5)
        super().server_close()


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
        if path.startswith("/status/"):
            job_id = path[len("/status/"):]
            try:
                payload = get_job_status(job_id, self.server.job_store, self.server.review_queue)
                self._send_json(payload, 200)
            except JobNotFoundError:
                self._send_json({"error": "Review not found."}, 404)
            return
        if path != "/":
            self._send_html(render_page(error="That page was not found."), 404)
            return
        query = parse_qs(urlparse(self.path).query)
        job_id = query.get("job_id", [None])[0]
        if job_id:
            try:
                job = self.server.job_store.get(job_id)
                self._send_html(render_page(job_state=job.state.value, upload_name=job.upload_name))
            except JobNotFoundError:
                self._send_html(render_page(error="That review has expired or was not found."))
            return
        self._send_html(render_page())

    def do_POST(self) -> None:
        if urlparse(self.path).path != "/review":
            self._send_json({"error": "That page was not found."}, 404)
            return
        try:
            length = int(self.headers.get("Content-Length", "0"))
            if length > MAX_REQUEST_BYTES:
                raise UploadValidationError("This upload request is too large.")
            content_type = self.headers.get("Content-Type", "")
            if not content_type.startswith("multipart/form-data"):
                raise UploadValidationError("Submit one photo using the upload form.")
            filename, content = _parse_photo(content_type, self.rfile.read(length))
            job = create_job_from_upload(
                filename,
                content,
                self.server.job_store,
                self.server.review_queue,
            )
            payload = get_job_status(job.job_id, self.server.job_store, self.server.review_queue)
            self._send_json(payload, 202)
        except QueueBusyError as error:
            self._send_json({"error": safe_error(error)}, 503)
        except (ValueError, UploadValidationError) as error:
            self._send_json({"error": safe_error(error)}, 400)
        except Exception:
            self._send_json({"error": safe_error(RuntimeError())}, 500)

    def log_message(self, format: str, *args) -> None:
        return


def create_server(
    host: str | None = None,
    port: int | None = None,
    revision: str | None = None,
    model_path: Path | str | None = None,
) -> PhotoGuidanceServer:
    resolved_host = host if host is not None else os.environ.get("HOST", DEFAULT_HOST)
    resolved_port = port if port is not None else int(os.environ.get("PORT", str(DEFAULT_PORT)))
    server = PhotoGuidanceServer((resolved_host, resolved_port), UploadHandler)
    server.release_revision = (
        revision
        or os.environ.get("APP_REVISION")
        or os.environ.get("RENDER_GIT_COMMIT")
        or os.environ.get("GITHUB_SHA")
        or DEFAULT_REVISION
    )
    server.model_path = Path(model_path or os.environ.get("MODEL_PATH", DEFAULT_MODEL_PATH))
    return server


def main() -> None:
    server = create_server()
    host, port = server.server_address
    print(f"Photo guidance available at http://{host}:{port}/")
    print(f"Revision: {server.release_revision}")
    print(f"Model path: {server.model_path}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
