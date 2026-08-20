import json
import os
from dataclasses import asdict
from pathlib import Path
from typing import Any


PROJECT_DIR = Path(__file__).resolve().parents[1]
CONVERTED_DIR = PROJECT_DIR / "converted_photos"
RESULTS_PATH = PROJECT_DIR / "results.jsonl"
CLEANED_RESULTS_PATH = PROJECT_DIR / "cleaned_results.json"
IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".bmp", ".tiff"}


def find_image_paths(converted_dir: Path = CONVERTED_DIR) -> list[Path]:
    return sorted(
        path
        for path in converted_dir.iterdir()
        if path.is_file() and path.suffix.lower() in IMAGE_EXTENSIONS
    )


def load_history(results_path: Path = RESULTS_PATH) -> list[Any]:
    if not results_path.exists():
        return []

    existing_content = results_path.read_text(encoding="utf-8").strip()
    if not existing_content:
        return []

    try:
        history = json.loads(existing_content)
        return history if isinstance(history, list) else [history]
    except json.JSONDecodeError:
        # Migrate legacy JSON Lines input into the normalized export format.
        return [json.loads(line) for line in existing_content.splitlines() if line.strip()]


def build_cleaned_payload(history: list[Any]) -> dict[str, Any]:
    cleaned_records: list[Any] = []
    seen_filenames: set[str] = set()
    duplicates_removed = 0

    for record in history:
        filename = record.get("image_filename") if isinstance(record, dict) else None
        if not isinstance(filename, str) or not filename.strip():
            cleaned_records.append(record)
            continue
        if filename in seen_filenames:
            duplicates_removed += 1
            continue
        seen_filenames.add(filename)
        cleaned_records.append(record)

    return {
        "statistics": {
            "total_records": len(history),
            "duplicates_removed": duplicates_removed,
            "unique_records": len(cleaned_records),
        },
        "records": cleaned_records,
    }


def write_json(path: Path, payload: Any) -> None:
    temporary_path = path.with_name(f".{path.name}.tmp")
    with temporary_path.open("w", encoding="utf-8") as file:
        json.dump(payload, file, indent=2, ensure_ascii=False)
        file.write("\n")
    os.replace(temporary_path, path)


def write_json_lines(path: Path, records: list[Any]) -> None:
    temporary_path = path.with_name(f".{path.name}.tmp")
    with temporary_path.open("w", encoding="utf-8") as file:
        for record in records:
            json.dump(record, file, ensure_ascii=False)
            file.write("\n")
    os.replace(temporary_path, path)


def export_results(
    history: list[Any],
    results_path: Path = RESULTS_PATH,
    cleaned_results_path: Path = CLEANED_RESULTS_PATH,
) -> None:
    """Write JSON Lines history and the deduplicated JSON export."""
    write_json_lines(results_path, history)
    write_json(cleaned_results_path, build_cleaned_payload(history))


def run(
    converted_dir: Path = CONVERTED_DIR,
    results_path: Path = RESULTS_PATH,
    cleaned_results_path: Path = CLEANED_RESULTS_PATH,
) -> None:
    image_paths = find_image_paths(converted_dir)
    if not image_paths:
        raise FileNotFoundError(f"No supported images found in {converted_dir}")

    from image_analysis import get_image_info
    from photo_analysis import build_analysis_result
    from recommendations import generate_recommendations
    from yolo import detect_objects

    history = load_history(results_path)
    for image_path in image_paths:
        try:
            info = get_image_info(str(image_path))
            result = build_analysis_result(info, detect_objects(str(image_path)))
            recommendations = generate_recommendations(result, info)

            print(f"\n{image_path.name}")
            print(result)
            print(recommendations)

            history.append(
                {
                    "image_filename": image_path.name,
                    "analysis": asdict(result),
                    "recommendations": asdict(recommendations),
                }
            )
        except Exception as error:
            print(f"Skipped {image_path.name}: {error}")

    export_results(history, results_path, cleaned_results_path)
    print(f"Saved results to {results_path}")
    print(f"Saved cleaned results to {cleaned_results_path}")


if __name__ == "__main__":
    run()
