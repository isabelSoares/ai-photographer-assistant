"""Validate results.jsonl and report duplicate image results."""

from __future__ import annotations

import argparse
import json
import sys
from collections import defaultdict
from dataclasses import asdict
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.generated.results_validation_contract import DuplicateGroup, ValidationStatistics

DEFAULT_RESULTS_PATH = PROJECT_ROOT / "results.jsonl"


def load_records(results_path: Path) -> list[object]:
    content = results_path.read_text(encoding="utf-8")
    if not content.strip():
        return []

    try:
        parsed = json.loads(content)
    except json.JSONDecodeError:
        records: list[object] = []
        for line_number, line in enumerate(content.splitlines(), start=1):
            if not line.strip():
                continue
            try:
                records.append(json.loads(line))
            except json.JSONDecodeError as error:
                raise ValueError(f"invalid JSON on line {line_number}: {error}") from error
        return records

    # Accept the previous array format as an input migration path, but always
    # Export results.jsonl as JSON Lines.
    if isinstance(parsed, list):
        return parsed
    return [parsed]


def verify_results(results_path: Path) -> int:
    if not results_path.exists():
        print(f"Results file not found: {results_path}", file=sys.stderr)
        return 2

    try:
        records = load_records(results_path)
    except (OSError, ValueError) as error:
        print(f"Invalid results file: {error}", file=sys.stderr)
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

    duplicate_groups = [
        DuplicateGroup(image_filename=filename, record_indexes=indexes)
        for filename, indexes in records_by_filename.items()
        if len(indexes) > 1
    ]

    statistics = ValidationStatistics(
        total_records=len(records),
        duplicates_removed=len(records) - len(cleaned_records),
        unique_records=len(cleaned_records),
    )
    cleaned_path = results_path.parent / "cleaned_results.json"
    cleaned_payload = {
        "statistics": asdict(statistics),
        "records": cleaned_records,
    }
    try:
        cleaned_path.write_text(json.dumps(cleaned_payload, indent=4) + "\n", encoding="utf-8")
    except OSError as error:
        print(f"Could not write cleaned results: {error}", file=sys.stderr)
        return 2

    if duplicate_groups:
        print("Duplicate images found:")
        for group in duplicate_groups:
            print(f"- {group.image_filename}: records {', '.join(map(str, group.record_indexes))}")
        return 1

    print("Results validation passed.")
    print(f"Records checked: {len(records)}")
    print("Duplicates found: 0")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "results_path",
        nargs="?",
        type=Path,
        default=DEFAULT_RESULTS_PATH,
        help="JSON Lines results file; defaults to the project results.jsonl",
    )
    args = parser.parse_args()
    return verify_results(args.results_path)


if __name__ == "__main__":
    raise SystemExit(main())
