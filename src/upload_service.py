from __future__ import annotations

import tempfile
from dataclasses import asdict, dataclass
from enum import StrEnum
from io import BytesIO
from pathlib import Path
from typing import Callable

from PIL import Image, UnidentifiedImageError


PROJECT_DIR = Path(__file__).resolve().parents[1]
DEFAULT_MODEL_PATH = PROJECT_DIR / "yolo11n.pt"
MAX_UPLOAD_BYTES = 10 * 1024 * 1024
SUPPORTED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".bmp", ".tiff", ".heic", ".heif"}


class ReviewState(StrEnum):
    IDLE = "idle"
    SELECTED = "selected"
    PROCESSING = "processing"
    COMPLETED = "completed"
    ERROR = "error"


@dataclass
class PhotoUpload:
    original_name: str
    media_type: str
    byte_size: int
    dimensions: tuple[int, int]
    temporary_path: Path | None = None
    state: ReviewState = ReviewState.SELECTED


@dataclass
class PhotoGuidanceResult:
    upload_name: str
    state: ReviewState
    summary: str | None = None
    subjects: list[dict] | None = None
    scenes: list[dict] | None = None
    tips: list[dict] | None = None
    uncertain: bool = False
    notice: str | None = None
    error_message: str | None = None


class UploadValidationError(ValueError):
    """Raised when an upload cannot be safely reviewed."""


def validate_upload(filename: str, content: bytes) -> PhotoUpload:
    """Validate bytes and return request metadata without retaining the upload."""
    display_name = Path(filename or "").name or "selected photo"
    if not content:
        raise UploadValidationError("Choose a photo before submitting.")
    if len(content) > MAX_UPLOAD_BYTES:
        raise UploadValidationError("This photo is larger than the 10 MiB upload limit.")
    if Path(display_name).suffix.lower() not in SUPPORTED_EXTENSIONS:
        raise UploadValidationError("That file format is not supported. Choose a JPG, PNG, WEBP, BMP, TIFF, or HEIC photo.")

    try:
        with Image.open(BytesIO(content)) as image:
            image.verify()
        with Image.open(BytesIO(content)) as image:
            dimensions = image.size
            media_type = image.get_format_mimetype() or "image/jpeg"
    except (UnidentifiedImageError, OSError, ValueError, Image.DecompressionBombError) as error:
        raise UploadValidationError("This file could not be read as a valid photo.") from error

    if not dimensions[0] or not dimensions[1]:
        raise UploadValidationError("This photo has invalid dimensions.")
    return PhotoUpload(display_name, media_type, len(content), dimensions)


def _write_normalized_image(content: bytes) -> Path:
    with Image.open(BytesIO(content)) as image:
        converted = image.convert("RGB")
        temporary = tempfile.NamedTemporaryFile(suffix=".jpg", delete=False)
        temporary_path = Path(temporary.name)
        try:
            converted.save(temporary, format="JPEG")
        finally:
            temporary.close()
    return temporary_path


def analyze_image(path: Path, model_path: Path = DEFAULT_MODEL_PATH) -> PhotoGuidanceResult:
    """Run the existing single-image pipeline without writing batch history."""
    try:
        from image_analysis import get_image_info
        from photo_analysis import build_analysis_result
        from recommendations import generate_recommendations
        from yolo import detect_objects
    except ModuleNotFoundError:
        from src.image_analysis import get_image_info
        from src.photo_analysis import build_analysis_result
        from src.recommendations import generate_recommendations
        from src.yolo import detect_objects

    image_info = get_image_info(str(path))
    analysis = build_analysis_result(image_info, detect_objects(str(path), model_path))
    recommendations = generate_recommendations(analysis, image_info)
    return guidance_from_analysis("", analysis, recommendations)


def guidance_from_analysis(upload_name: str, analysis, recommendations) -> PhotoGuidanceResult:
    tips = [asdict(item) for item in recommendations.items]
    if not tips:
        raise RuntimeError("Analysis did not produce any usable guidance.")
    return PhotoGuidanceResult(
        upload_name=upload_name,
        state=ReviewState.COMPLETED,
        summary=analysis.summary,
        subjects=[asdict(item) for item in analysis.subjects],
        scenes=[asdict(item) for item in analysis.scene_attributes],
        tips=tips,
        uncertain=analysis.uncertain or recommendations.uncertain,
        notice=analysis.notice,
    )


def review_upload(
    filename: str,
    content: bytes,
    analyzer: Callable[[Path], PhotoGuidanceResult] | None = None,
) -> PhotoGuidanceResult:
    """Validate, temporarily normalize, analyze, and always remove the upload."""
    upload = validate_upload(filename, content)
    upload.state = ReviewState.PROCESSING
    temporary_path = _write_normalized_image(content)
    upload.temporary_path = temporary_path
    try:
        result = (analyzer or analyze_image)(temporary_path)
        result.upload_name = upload.original_name
        result.state = ReviewState.COMPLETED
        return result
    except Exception:
        return PhotoGuidanceResult(
            upload_name=upload.original_name,
            state=ReviewState.ERROR,
            error_message="The photo could not be analyzed. Try again or choose another photo.",
        )
    finally:
        temporary_path.unlink(missing_ok=True)
