from pathlib import Path

from PIL import Image
import pillow_heif

# 1. Globally enable HEIC support for Pillow
pillow_heif.register_heif_opener()

PROJECT_DIR = Path(__file__).resolve().parents[1]
DEFAULT_MODEL_PATH = PROJECT_DIR / "yolo11n.pt"
_model = None
_model_path: Path | None = None


def _load_model(model_path: Path):
    global _model, _model_path
    if _model is None or _model_path != model_path:
        from ultralytics import YOLO

        if not model_path.exists():
            raise FileNotFoundError(f"YOLO model not found: {model_path}")
        _model = YOLO(str(model_path))
        _model_path = model_path
    return _model


def detect_objects(image_path: str, model_path: Path = DEFAULT_MODEL_PATH):
    model = _load_model(model_path)
    with Image.open(image_path) as img:
        results = model(img)
    detections = []

    for result in results:
        for box in result.boxes:
            detections.append({
                "class": result.names[int(box.cls)],
                "confidence": float(box.conf),
            })

    return detections
