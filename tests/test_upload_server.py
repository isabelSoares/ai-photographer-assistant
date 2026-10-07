import json
import os
import threading
import time
import unittest
import unittest.mock
from http.client import HTTPConnection
from io import BytesIO
from pathlib import Path
from PIL import Image

from src.upload_jobs import JobState
from src.upload_server import create_server, result_payload
from src.upload_service import PhotoGuidanceResult, ReviewState


def multipart(filename: str, content: bytes) -> tuple[str, bytes]:
    boundary = "----photo-test-boundary"
    body = (f"--{boundary}\r\nContent-Disposition: form-data; name=\"photo\"; filename=\"{filename}\"\r\nContent-Type: image/jpeg\r\n\r\n").encode() + content + f"\r\n--{boundary}--\r\n".encode()
    return f"multipart/form-data; boundary={boundary}", body


def valid_jpeg_bytes() -> bytes:
    image = Image.new("RGB", (10, 10), color="red")
    buffer = BytesIO()
    image.save(buffer, format="JPEG")
    return buffer.getvalue()


def stub_analyzer(path: Path) -> PhotoGuidanceResult:
    return PhotoGuidanceResult(
        upload_name="photo.jpg",
        state=ReviewState.COMPLETED,
        summary="A person was detected.",
        tips=[{"text": "Try an off-center composition.", "category": "composition", "reason": "A person was detected."}],
        uncertain=True,
    )


class UploadServerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.server = create_server(port=0, revision="development")
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()
        cls.host, cls.port = cls.server.server_address

    @classmethod
    def tearDownClass(cls) -> None:
        cls.server.shutdown()
        cls.server.server_close()
        cls.thread.join()

    def setUp(self) -> None:
        self.server.review_queue._jobs.clear()
        self.server.job_store._jobs.clear()
        self.server.analysis_worker.analyzer = stub_analyzer

    def request(self, method: str, path: str, body: bytes = b"", headers: dict | None = None):
        connection = HTTPConnection(self.host, self.port, timeout=5)
        connection.request(method, path, body=body, headers=headers or {})
        response = connection.getresponse()
        content = response.read().decode()
        connection.close()
        return response.status, content

    def test_get_returns_labeled_upload_area(self) -> None:
        status, body = self.request("GET", "/")
        self.assertEqual(status, 200)
        self.assertIn('id="photo"', body)
        self.assertIn("Maximum 10 MiB", body)
        self.assertIn("No photo selected", body)

    def test_health_endpoint_reports_revision_and_model_readiness(self) -> None:
        status, body = self.request("GET", "/healthz")
        self.assertEqual(status, 200)
        self.assertIn('"status": "healthy"', body)
        self.assertIn('"revision": "development"', body)

    def test_health_endpoint_uses_render_git_commit_revision(self) -> None:
        env = {"RENDER_GIT_COMMIT": "abc123render"}
        with unittest.mock.patch.dict(os.environ, env, clear=False):
            server = create_server(port=0, revision=None)
        self.assertEqual(server.release_revision, "abc123render")
        server.server_close()

    def test_health_endpoint_uses_app_revision_over_render(self) -> None:
        env = {"APP_REVISION": "app-sha", "RENDER_GIT_COMMIT": "render-sha"}
        with unittest.mock.patch.dict(os.environ, env, clear=False):
            server = create_server(port=0, revision=None)
        self.assertEqual(server.release_revision, "app-sha")
        server.server_close()

    def test_health_endpoint_reports_unhealthy_when_model_is_missing(self) -> None:
        server = create_server(port=0, model_path=Path("/tmp/missing-yolo-model.pt"))
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            host, port = server.server_address
            connection = HTTPConnection(host, port, timeout=5)
            connection.request("GET", "/healthz")
            response = connection.getresponse()
            body = response.read().decode()
            connection.close()
            self.assertEqual(response.status, 503)
            self.assertIn('"status": "unhealthy"', body)
        finally:
            server.shutdown()
            server.server_close()
            thread.join()

    def test_invalid_upload_returns_replacement_error(self) -> None:
        content_type, body = multipart("photo.gif", b"not-an-image")
        status, response = self.request("POST", "/review", body, {"Content-Type": content_type, "Content-Length": str(len(body))})
        self.assertEqual(status, 400)
        data = json.loads(response)
        self.assertIn("not supported", data["error"])
        self.assertIn("JPG", data["error"])

    def test_valid_upload_returns_202_with_job_id_and_queue_state(self) -> None:
        content_type, body = multipart("photo.jpg", valid_jpeg_bytes())
        status, response = self.request("POST", "/review", body, {"Content-Type": content_type, "Content-Length": str(len(body))})
        self.assertEqual(status, 202)
        data = json.loads(response)
        self.assertIn("job_id", data)
        self.assertEqual(data["state"], JobState.QUEUED.value)
        self.assertEqual(data["queue_position"], 1)
        self.assertIn("message", data)

    def test_status_endpoint_returns_completed_state(self) -> None:
        content_type, body = multipart("photo.jpg", valid_jpeg_bytes())
        status, response = self.request("POST", "/review", body, {"Content-Type": content_type, "Content-Length": str(len(body))})
        job_id = json.loads(response)["job_id"]
        data = self._poll_status(job_id, {JobState.COMPLETED.value, JobState.FAILED.value})
        self.assertEqual(data["state"], JobState.COMPLETED.value)
        self.assertEqual(data["result"]["summary"], "A person was detected.")

    def _poll_status(self, job_id: str, terminal_states: set[str], timeout: float = 5.0) -> dict:
        deadline = time.time() + timeout
        while time.time() < deadline:
            status, response = self.request("GET", f"/status/{job_id}")
            self.assertEqual(status, 200)
            data = json.loads(response)
            if data["state"] in terminal_states:
                return data
            time.sleep(0.05)
        self.fail(f"Job {job_id} did not reach a terminal state in time")

    def test_status_endpoint_returns_404_for_unknown_job(self) -> None:
        status, response = self.request("GET", "/status/unknownjobid")
        self.assertEqual(status, 404)
        self.assertIn("error", json.loads(response))

    def test_second_upload_is_queued_with_position(self) -> None:
        # Slow analyzer keeps first job in processing for a long time.
        self.server.analysis_worker.analyzer = lambda path: time.sleep(2) or stub_analyzer(path)

        content_type, body = multipart("first.jpg", valid_jpeg_bytes())
        status, response = self.request("POST", "/review", body, {"Content-Type": content_type, "Content-Length": str(len(body))})
        first_id = json.loads(response)["job_id"]

        # Wait until the first job is actually being processed.
        self._poll_status(first_id, {JobState.PROCESSING.value})

        content_type2, body2 = multipart("second.jpg", valid_jpeg_bytes())
        status2, response2 = self.request("POST", "/review", body2, {"Content-Type": content_type2, "Content-Length": str(len(body2))})
        self.assertEqual(status2, 202)
        data = json.loads(response2)
        self.assertEqual(data["queue_position"], 1)
        self.assertIn("second.jpg", data["message"])

        # Restore fast analyzer and wait for both to complete.
        self.server.analysis_worker.analyzer = stub_analyzer
        self._poll_status(first_id, {JobState.COMPLETED.value, JobState.FAILED.value})

    def test_queue_overflow_returns_503(self) -> None:
        self.server.analysis_worker.analyzer = lambda path: time.sleep(10) or stub_analyzer(path)
        for i in range(10):
            content_type, body = multipart(f"photo{i}.jpg", valid_jpeg_bytes())
            self.request("POST", "/review", body, {"Content-Type": content_type, "Content-Length": str(len(body))})
        content_type, body = multipart("overflow.jpg", valid_jpeg_bytes())
        status, response = self.request("POST", "/review", body, {"Content-Type": content_type, "Content-Length": str(len(body))})
        self.assertEqual(status, 503)
        self.assertIn("busy", json.loads(response)["error"].lower())
        self.server.analysis_worker.analyzer = stub_analyzer

    def test_healthz_remains_healthy_while_jobs_are_processing(self) -> None:
        self.server.analysis_worker.analyzer = lambda path: time.sleep(1) or stub_analyzer(path)
        content_type, body = multipart("busy.jpg", valid_jpeg_bytes())
        self.request("POST", "/review", body, {"Content-Type": content_type, "Content-Length": str(len(body))})
        status, response = self.request("GET", "/healthz")
        self.assertEqual(status, 200)
        self.assertIn('"status": "healthy"', response)
        self.server.analysis_worker.analyzer = stub_analyzer

    def test_result_payload_matches_contract_fields(self) -> None:
        payload = result_payload(PhotoGuidanceResult("photo.jpg", ReviewState.ERROR, error_message="Try again."))
        self.assertEqual(payload["state"], "error")
        self.assertIn("tips", payload)
        self.assertIn("uncertain", payload)
        self.assertEqual(payload["error_message"], "Try again.")

    def test_page_escapes_upload_name_in_initial_render(self) -> None:
        content_type, body = multipart("<script>alert.jpg", valid_jpeg_bytes())
        status, response = self.request("POST", "/review", body, {"Content-Type": content_type, "Content-Length": str(len(body))})
        job_id = json.loads(response)["job_id"]
        status, page = self.request("GET", f"/?job_id={job_id}")
        self.assertEqual(status, 200)
        self.assertNotIn("<script>alert", page)
        self.assertIn("&lt;script&gt;alert", page)


if __name__ == "__main__":
    unittest.main()
