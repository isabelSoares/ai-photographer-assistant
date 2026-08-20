import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SCRIPT = PROJECT_ROOT / "scripts" / "verify_results.py"


class VerifyResultsTests(unittest.TestCase):
    @staticmethod
    def json_lines(records: list[object]) -> str:
        return "\n".join(json.dumps(record) for record in records) + "\n"

    def run_verifier(self, content: str) -> subprocess.CompletedProcess[str]:
        with tempfile.TemporaryDirectory() as directory:
            results_path = Path(directory) / "results.jsonl"
            results_path.write_text(content, encoding="utf-8")
            return subprocess.run(
                [sys.executable, str(SCRIPT), str(results_path)],
                capture_output=True,
                text=True,
                check=False,
            )

    def test_unique_filenames_pass(self) -> None:
        completed = self.run_verifier(
            self.json_lines([
                {"image_filename": "one.jpg"},
                {"image_filename": "two.jpg"},
            ])
        )
        self.assertEqual(completed.returncode, 0)
        self.assertIn("Duplicates found: 0", completed.stdout)

    def test_duplicate_filenames_fail_with_indexes(self) -> None:
        completed = self.run_verifier(
            self.json_lines([
                {"image_filename": "one.jpg"},
                {"image_filename": "test.jpg"},
                {"image_filename": "other.jpg"},
                {"image_filename": "test.jpg"},
            ])
        )
        self.assertEqual(completed.returncode, 1)
        self.assertIn("- test.jpg: records 2, 4", completed.stdout)

    def test_duplicate_results_are_cleaned_and_keep_first_record(self) -> None:
        records = [
            {"image_filename": "one.jpg", "value": 1},
            {"image_filename": "test.jpg", "value": 2},
            {"image_filename": "test.jpg", "value": 3},
        ]
        with tempfile.TemporaryDirectory() as directory:
            results_path = Path(directory) / "results.jsonl"
            results_path.write_text(self.json_lines(records), encoding="utf-8")
            subprocess.run([sys.executable, str(SCRIPT), str(results_path)], check=False)

            cleaned = json.loads((results_path.parent / "cleaned_results.json").read_text())
            self.assertEqual(cleaned["statistics"]["total_records"], 3)
            self.assertEqual(cleaned["statistics"]["duplicates_removed"], 1)
            self.assertEqual(cleaned["statistics"]["unique_records"], 2)
            self.assertEqual(cleaned["records"][1]["value"], 2)

    def test_cleaning_does_not_modify_original_results(self) -> None:
        content = self.json_lines([
            {"image_filename": "one.jpg"},
            {"image_filename": "one.jpg"},
        ])
        with tempfile.TemporaryDirectory() as directory:
            results_path = Path(directory) / "results.jsonl"
            results_path.write_text(content, encoding="utf-8")
            original = results_path.read_bytes()
            subprocess.run([sys.executable, str(SCRIPT), str(results_path)], check=False)
            self.assertEqual(results_path.read_bytes(), original)

    def test_invalid_json_returns_two(self) -> None:
        completed = self.run_verifier("not json")
        self.assertEqual(completed.returncode, 2)

    def test_missing_results_file_returns_two(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            missing_path = Path(directory) / "missing.json"
            completed = subprocess.run(
                [sys.executable, str(SCRIPT), str(missing_path)],
                capture_output=True,
                text=True,
                check=False,
            )
        self.assertEqual(completed.returncode, 2)

    def test_single_json_lines_object_is_valid(self) -> None:
        completed = self.run_verifier(json.dumps({"image_filename": "one.jpg"}) + "\n")
        self.assertEqual(completed.returncode, 0)

    def test_legacy_json_array_is_still_accepted(self) -> None:
        completed = self.run_verifier(json.dumps([{"image_filename": "one.jpg"}]))
        self.assertEqual(completed.returncode, 0)

    def test_each_record_must_be_an_object(self) -> None:
        completed = self.run_verifier(json.dumps("one.jpg") + "\n")
        self.assertEqual(completed.returncode, 2)

    def test_filename_must_not_be_blank(self) -> None:
        completed = self.run_verifier(json.dumps({"image_filename": "  "}) + "\n")
        self.assertEqual(completed.returncode, 2)

    def test_missing_filename_returns_two(self) -> None:
        completed = self.run_verifier(json.dumps({"analysis": {}}) + "\n")
        self.assertEqual(completed.returncode, 2)

    def test_results_file_is_not_modified(self) -> None:
        content = json.dumps({"image_filename": "one.jpg"}) + "\n"
        with tempfile.TemporaryDirectory() as directory:
            results_path = Path(directory) / "results.jsonl"
            results_path.write_text(content, encoding="utf-8")
            original = results_path.read_bytes()
            subprocess.run(
                [sys.executable, str(SCRIPT), str(results_path)],
                check=False,
            )
            self.assertEqual(results_path.read_bytes(), original)


if __name__ == "__main__":
    unittest.main()
