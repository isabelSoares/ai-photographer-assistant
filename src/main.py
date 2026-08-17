import json
from dataclasses import asdict
import os

from image_analysis import get_image_info
from yolo import detect_objects
from photo_analysis import build_analysis_result
from recommendations import generate_recommendations

project_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
converted_dir = os.path.join(project_dir, "converted_photos")
results_path = os.path.join(project_dir, "results.json")
image_extensions = {".jpg", ".jpeg", ".png", ".webp", ".bmp", ".tiff"}
image_paths = sorted(
    os.path.join(converted_dir, filename)
    for filename in os.listdir(converted_dir)
    if os.path.splitext(filename)[1].lower() in image_extensions
)

if not image_paths:
    raise FileNotFoundError(f"No supported images found in {converted_dir}")

history = []
if os.path.exists(results_path):
    with open(results_path, "r", encoding="utf-8") as file:
        existing_content = file.read().strip()
    if existing_content:
        try:
            history = json.loads(existing_content)
            if not isinstance(history, list):
                history = [history]
        except json.JSONDecodeError:
            # Migrate the previous JSON Lines format to the JSON array format.
            history = [json.loads(line) for line in existing_content.splitlines() if line.strip()]

for image_path in image_paths:
    try:
        info = get_image_info(image_path)
        result = build_analysis_result(info, detect_objects(image_path))
        recommendations = generate_recommendations(result, info)

        print(f"\n{os.path.basename(image_path)}")
        print(result)
        print(recommendations)

        history.append(
            {
                "image_filename": os.path.basename(image_path),
                "analysis": asdict(result),
                "recommendations": asdict(recommendations),
            }
        )
    except Exception as error:
        print(f"Skipped {os.path.basename(image_path)}: {error}")

with open(results_path, "w", encoding="utf-8") as file:
    file.write("[\n")
    file.write(",\n".join(json.dumps(item) for item in history))
    file.write("\n]\n")

print(f"Saved results to {results_path}")
