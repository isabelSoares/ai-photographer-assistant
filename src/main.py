import json
from dataclasses import asdict
import os

from image_analysis import get_image_info
from yolo import detect_objects
from photo_analysis import build_analysis_result
from recommendations import generate_recommendations

image_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "./../converted_photos/IMG_8982.jpg"))

if not os.path.exists(image_path):
    raise FileNotFoundError(f"Image file not found: {image_path}")

info = get_image_info(image_path)
result = build_analysis_result(info, detect_objects(image_path))
recommendations = generate_recommendations(result, info)

print(result)
print(recommendations)

results_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "../results.json"))
with open(results_path, "a", encoding="utf-8") as file:
    payload = {
        "image_filename": os.path.basename(image_path),
        "analysis": asdict(result),
        "recommendations": asdict(recommendations),
    }
    file.write(json.dumps(payload))
    file.write("\n")

print(f"Saved results to {results_path}")
