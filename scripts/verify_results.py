"""Validate results.json and report duplicate image results."""

from __future__ import annotations

import argparse
import json
import sys
from collections import defaultdict
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_RESULTS_PATH = PROJECT_ROOT / "results.json"


def verify_results(results_path: Path) -> int:
    if not results_path.exists():
        print(f"Results file not found: {results_path}", file=sys.stderr)
        return 2

    try:
        with results_path.open("r", encoding="utf-8") as file:
            records = json.load(file)
    except (OSError, json.JSONDecodeError) as error:
        print(f"Invalid results file: {error}", file=sys.stderr)
        return 2

    if not isinstance(records, list):
        print("Invalid results file: root value must be a JSON array", file=sys.stderr)
        return 2

    records_by_filename: dict[str, list[int]] = defaultdict(list)
    cleaned_records: list[dict] = []
    seen_filenames: set[str] = set()
    for index, record in enumerate(records, start=1):
        if not isinstance(record, dict):
            print(f"Invalid results file: record {index} must be an object", file=sys.stderr)
            return 2
        filename = record.get("image_filename")
        if not isinstance(filename, str) or not filename.strip():
            print(
                f"Invalid results file: record {index} needs a non-empty image_filename",
                file=sys.stderr,
            )
            return 2
        records_by_filename[filename].append(index)
        if filename not in seen_filenames:
            cleaned_records.append(record)
            seen_filenames.add(filename)

    duplicates = {
        filename: indexes
        for filename, indexes in records_by_filename.items()
        if len(indexes) > 1
    }
    cleaned_path = results_path.parent / "cleaned_results.json"
    cleaned_payload = {
        "statistics": {
            "total_records": len(records),
            "duplicates_removed": len(records) - len(cleaned_records),
            "unique_records": len(cleaned_records),
        },
        "records": cleaned_records,
    }
    try:
        cleaned_path.write_text(json.dumps(cleaned_payload, indent=4) + "\n", encoding="utf-8")
    except OSError as error:
        print(f"Could not write cleaned results: {error}", file=sys.stderr)
        return 2

    if duplicates:
        print("Duplicate images found:")
        for filename, indexes in duplicates.items():
            print(f"- {filename}: records {', '.join(map(str, indexes))}")
        print(f"Cleaned results saved to {cleaned_path}")
        return 1

    print("Results validation passed.")
    print(f"Records checked: {len(records)}")
    print("Duplicates found: 0")
    print(f"Cleaned results saved to {cleaned_path}")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "results_path",
        nargs="?",
        type=Path,
        default=DEFAULT_RESULTS_PATH,
        help="JSON results file; defaults to the project results.json",
    )
    args = parser.parse_args()
    return verify_results(args.results_path)


if __name__ == "__main__":
    raise SystemExit(main())
