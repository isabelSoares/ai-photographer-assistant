import threading
import unittest
from http.client import HTTPConnection
from unittest.mock import patch

from src.upload_server import create_server, result_payload
from src.upload_service import PhotoGuidanceResult, ReviewState


def multipart(filename: str, content: bytes) -> tuple[str, bytes]:
    boundary = "----photo-test-boundary"
    body = (f"--{boundary}\r\nContent-Disposition: form-data; name=\"photo\"; filename=\"{filename}\"\r\nContent-Type: image/jpeg\r\n\r\n").encode() + content + f"\r\n--{boundary}--\r\n".encode()
    return f"multipart/form-data; boundary={boundary}", body


class UploadServerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.server = create_server(port=0)
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()
        cls.host, cls.port = cls.server.server_address

    @classmethod
    def tearDownClass(cls) -> None:
        cls.server.shutdown()
        cls.server.server_close()
        cls.thread.join()

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

    def test_invalid_upload_returns_replacement_error(self) -> None:
        content_type, body = multipart("photo.gif", b"not-an-image")
        status, response = self.request("POST", "/review", body, {"Content-Type": content_type, "Content-Length": str(len(body))})
        self.assertEqual(status, 400)
        self.assertIn("Choose another photo", response)
        self.assertIn("not supported", response)

    def test_completed_result_renders_safe_actionable_guidance(self) -> None:
        result = PhotoGuidanceResult("<photo>.jpg", ReviewState.COMPLETED, summary="A person was detected.", tips=[{"text": "Try an off-center composition.", "category": "composition", "reason": "A person was detected."}], uncertain=True)
        content_type, body = multipart("photo.jpg", b"valid")
        with patch("src.upload_server.review_upload", return_value=result):
            status, response = self.request("POST", "/review", body, {"Content-Type": content_type, "Content-Length": str(len(body))})
        self.assertEqual(status, 200)
        self.assertIn("&lt;photo&gt;.jpg", response)
        self.assertNotIn("<photo>.jpg", response)
        self.assertIn("Try an off-center composition", response)
        self.assertIn("tentative", response)

    def test_result_payload_matches_contract_fields(self) -> None:
        payload = result_payload(PhotoGuidanceResult("photo.jpg", ReviewState.ERROR, error_message="Try again."))
        self.assertEqual(payload["state"], "error")
        self.assertIn("tips", payload)
        self.assertIn("uncertain", payload)
        self.assertEqual(payload["error_message"], "Try again.")

    def test_analysis_error_offers_retry_and_replacement(self) -> None:
        result = PhotoGuidanceResult("photo.jpg", ReviewState.ERROR, error_message="The photo could not be analyzed.")
        content_type, body = multipart("photo.jpg", b"valid")
        with patch("src.upload_server.review_upload", return_value=result):
            status, response = self.request("POST", "/review", body, {"Content-Type": content_type, "Content-Length": str(len(body))})
        self.assertEqual(status, 500)
        self.assertIn("Try again", response)
        self.assertIn("Choose another photo", response)
        self.assertNotIn("Review for photo.jpg", response)


if __name__ == "__main__":
    unittest.main()
