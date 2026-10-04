import unittest
from io import BytesIO
from pathlib import Path

from PIL import Image

from src.generated.photo_analysis_contract import Detection, PhotoAnalysisResult
from src.generated.recommendations_contract import PhotographyRecommendations, Recommendation
from src.upload_service import MAX_UPLOAD_BYTES, ReviewState, UploadValidationError, guidance_from_analysis, review_upload, validate_upload


def jpeg_bytes() -> bytes:
    stream = BytesIO()
    Image.new("RGB", (24, 18), "orange").save(stream, format="JPEG")
    return stream.getvalue()


class UploadServiceTests(unittest.TestCase):
    def test_valid_upload_returns_metadata_and_normalizes_name(self) -> None:
        upload = validate_upload("folder/photo.jpg", jpeg_bytes())
        self.assertEqual(upload.original_name, "photo.jpg")
        self.assertEqual(upload.dimensions, (24, 18))
        self.assertEqual(upload.state, ReviewState.SELECTED)

    def test_empty_unsupported_malformed_and_oversized_uploads_are_rejected(self) -> None:
        cases = (("photo.jpg", b"", "Choose a photo"), ("photo.gif", jpeg_bytes(), "not supported"), ("photo.jpg", b"not an image", "could not be read"), ("photo.jpg", b"x" * (MAX_UPLOAD_BYTES + 1), "10 MiB"))
        for filename, content, message in cases:
            with self.subTest(filename=filename), self.assertRaisesRegex(UploadValidationError, message):
                validate_upload(filename, content)

    def test_review_removes_temporary_file_on_success(self) -> None:
        captured: list[Path] = []

        def analyzer(path: Path):
            captured.append(path)
            return type("Result", (), {"state": ReviewState.COMPLETED, "upload_name": "", "tips": [{"text": "Try a new angle"}]})()

        result = review_upload("photo.jpg", jpeg_bytes(), analyzer)
        self.assertEqual(result.upload_name, "photo.jpg")
        self.assertFalse(captured[0].exists())

    def test_review_returns_safe_error_and_removes_temporary_file(self) -> None:
        captured: list[Path] = []

        def analyzer(path: Path):
            captured.append(path)
            raise RuntimeError("secret model path")

        result = review_upload("photo.jpg", jpeg_bytes(), analyzer)
        self.assertEqual(result.state, ReviewState.ERROR)
        self.assertNotIn("secret", result.error_message or "")
        self.assertFalse(captured[0].exists())

    def test_guidance_mapping_preserves_fallback_and_uncertainty(self) -> None:
        analysis = PhotoAnalysisResult("A photo with uncertain content.", [Detection("Person", 0.55, True)], [], True, "Review the image carefully.")
        recommendations = PhotographyRecommendations([Recommendation("Try a clearer composition.", "practice", "Limited analysis")], True)
        result = guidance_from_analysis("photo.jpg", analysis, recommendations)
        self.assertEqual(len(result.tips), 1)
        self.assertTrue(result.uncertain)
        self.assertEqual(result.notice, "Review the image carefully.")


if __name__ == "__main__":
    unittest.main()
