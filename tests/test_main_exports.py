import json
import tempfile
import unittest
from pathlib import Path

from src.main import build_cleaned_payload, export_results, load_history, run


class MainExportTests(unittest.TestCase):
    def test_exports_are_valid_json_with_expected_shapes(self) -> None:
        history = [
            {"image_filename": "first.jpg", "value": 1},
            {"image_filename": "first.jpg", "value": 2},
            {"image_filename": "second.jpg", "value": 3},
        ]

        with tempfile.TemporaryDirectory() as directory:
            results_path = Path(directory) / "results.jsonl"
            cleaned_path = Path(directory) / "cleaned_results.json"
            export_results(history, results_path, cleaned_path)

            result_lines = results_path.read_text(encoding="utf-8").splitlines()
            results = [json.loads(line) for line in result_lines if line.strip()]
            cleaned = json.loads(cleaned_path.read_text(encoding="utf-8"))

        self.assertEqual(results, history)
        self.assertEqual(cleaned["statistics"]["total_records"], 3)
        self.assertEqual(cleaned["statistics"]["duplicates_removed"], 1)
        self.assertEqual(cleaned["statistics"]["unique_records"], 2)
        self.assertEqual(cleaned["records"][0]["value"], 1)

    def test_json_lines_are_loaded_and_exported_as_json_lines(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            results_path = Path(directory) / "results.jsonl"
            results_path.write_text(
                '{"image_filename":"first.jpg"}\n{"image_filename":"second.jpg"}\n',
                encoding="utf-8",
            )

            history = load_history(results_path)
            export_results(history, results_path, Path(directory) / "cleaned_results.json")
            exported = [
                json.loads(line)
                for line in results_path.read_text(encoding="utf-8").splitlines()
                if line.strip()
            ]

        self.assertEqual(exported, history)
        self.assertIsInstance(exported, list)

    def test_legacy_json_array_is_exported_as_json_lines(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            results_path = Path(directory) / "results.jsonl"
            results_path.write_text(
                json.dumps([{"image_filename": "first.jpg"}, {"image_filename": "second.jpg"}]),
                encoding="utf-8",
            )

            history = load_history(results_path)
            export_results(history, results_path, Path(directory) / "cleaned_results.json")
            exported_lines = results_path.read_text(encoding="utf-8").splitlines()

        self.assertEqual([json.loads(line) for line in exported_lines], history)
        self.assertEqual(len(exported_lines), 2)

    def test_cleaned_payload_keeps_records_without_filename_without_crashing(self) -> None:
        payload = build_cleaned_payload([{"value": 1}, {"image_filename": "one.jpg"}])

        self.assertEqual(payload["statistics"]["total_records"], 2)
        self.assertEqual(payload["statistics"]["duplicates_removed"], 0)
        self.assertEqual(len(payload["records"]), 2)

    def test_no_supported_images_raises_without_creating_exports(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            converted_dir = Path(directory) / "converted_photos"
            converted_dir.mkdir()
            results_path = Path(directory) / "results.jsonl"
            cleaned_path = Path(directory) / "cleaned_results.json"

            with self.assertRaises(FileNotFoundError):
                run(converted_dir, results_path, cleaned_path)

            self.assertFalse(results_path.exists())
            self.assertFalse(cleaned_path.exists())

    def test_malformed_json_lines_report_the_line_number(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            results_path = Path(directory) / "results.jsonl"
            results_path.write_text('{"image_filename":"one.jpg"}\nnot json\n', encoding="utf-8")

            with self.assertRaisesRegex(ValueError, "line 2"):
                load_history(results_path)

    def test_skip_existing_does_not_create_empty_exports(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            converted_dir = Path(directory) / "converted_photos"
            converted_dir.mkdir()
            (converted_dir / "one.jpg").write_bytes(b"not used")
            results_path = Path(directory) / "results.jsonl"
            results_path.write_text('{"image_filename":"one.jpg"}\n', encoding="utf-8")
            cleaned_path = Path(directory) / "cleaned_results.json"

            with self.assertRaisesRegex(RuntimeError, "No images were successfully analyzed"):
                run(converted_dir, results_path, cleaned_path, skip_existing=True)

            self.assertFalse(cleaned_path.exists())


if __name__ == "__main__":
    unittest.main()
