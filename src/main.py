from image_analysis import get_image_info
from yolo import detect_objects
import os

image_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "./../converted_photos/test.jpg"))

if not os.path.exists(image_path):
    raise FileNotFoundError(f"Image file not found: {image_path}")

info = get_image_info(image_path)
detections = detect_objects(image_path)

print(info)
print(detections)