from PIL import Image
from ultralytics import YOLO
import pillow_heif

# 1. Globally enable HEIC support for Pillow
pillow_heif.register_heif_opener()

# 2. Load the YOLO model
model = YOLO("yolo11n.pt")


def detect_objects(image_path: str):
    try:
        # 3. Open the image using Pillow (Handles HEIC, PNG, JPG, etc.)
        with Image.open(image_path) as img:
            # 4. Pass the Pillow Image object directly to YOLO
            results = model(img)
    except Exception as e:
        print(f"Error opening image {image_path}: {e}")
        return []

    detections = []

    for result in results:
        for box in result.boxes:
            detections.append({
                "class": result.names[int(box.cls)],
                "confidence": float(box.conf),
            })

    return detections
