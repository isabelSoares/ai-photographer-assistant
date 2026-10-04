import argparse
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
    except json.JSONDecodeError:
        # Migrate legacy JSON Lines input into the normalized export format.
        history = []
        for line_number, line in enumerate(existing_content.splitlines(), start=1):
            if not line.strip():
                continue
            try:
                history.append(json.loads(line))
            except json.JSONDecodeError as error:
                raise ValueError(f"Invalid JSON on line {line_number}: {error}") from error

    if isinstance(history, list):
        return history
    if isinstance(history, dict):
        return [history]
    raise ValueError("Results history must contain JSON objects")


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
    model_path: Path | None = None,
    skip_existing: bool = False,
) -> int:
    image_paths = find_image_paths(converted_dir)
    if not image_paths:
        raise FileNotFoundError(f"No supported images found in {converted_dir}")

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

    history = load_history(results_path)
    existing_filenames = {
        record.get("image_filename")
        for record in history
        if isinstance(record, dict) and isinstance(record.get("image_filename"), str)
    }
    processed = 0
    failures = 0
    for image_path in image_paths:
        if skip_existing and image_path.name in existing_filenames:
            print(f"Skipped {image_path.name}: already present in history")
            continue
        try:
            info = get_image_info(str(image_path))
            result = build_analysis_result(
                info,
                detect_objects(str(image_path), model_path or PROJECT_DIR / "yolo11n.pt"),
            )
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
            processed += 1
        except Exception as error:
            failures += 1
            print(f"Skipped {image_path.name}: {error}")

    if processed == 0:
        raise RuntimeError("No images were successfully analyzed; result files were not written")

    export_results(history, results_path, cleaned_results_path)
    print(f"Saved results to {results_path}")
    print(f"Saved cleaned results to {cleaned_results_path}")
    if failures:
        print(f"Completed with {failures} failed image(s)")
        return 1
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Analyze converted photographs in a directory")
    parser.add_argument("--input-dir", type=Path, default=CONVERTED_DIR)
    parser.add_argument("--results", type=Path, default=RESULTS_PATH)
    parser.add_argument("--cleaned-results", type=Path, default=CLEANED_RESULTS_PATH)
    parser.add_argument("--model", type=Path, default=PROJECT_DIR / "yolo11n.pt")
    parser.add_argument(
        "--skip-existing",
        action="store_true",
        help="Do not analyze filenames already present in the results history",
    )
    args = parser.parse_args()
    try:
        return run(
            args.input_dir,
            args.results,
            args.cleaned_results,
            args.model,
            args.skip_existing,
        )
    except (FileNotFoundError, ValueError, RuntimeError) as error:
        parser.error(str(error))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
