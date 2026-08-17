from image_analysis import get_image_info
from yolo import detect_objects
from photo_analysis import build_analysis_result
import os

image_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "./../converted_photos/IMG_8982.jpg"))

if not os.path.exists(image_path):
    raise FileNotFoundError(f"Image file not found: {image_path}")

info = get_image_info(image_path)
result = build_analysis_result(info, detect_objects(image_path))

print(result)
