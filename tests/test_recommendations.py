import sys
import unittest
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from generated.photo_analysis_contract import AnalysisSignals, Detection, PhotoAnalysisResult
from photo_analysis import build_analysis_result
from recommendations import generate_recommendations


def recommendation_categories(result: PhotoAnalysisResult, image_info: dict) -> set[str]:
    return {item.category for item in generate_recommendations(result, image_info).items}


class RecommendationsTests(unittest.TestCase):
    def test_person_gets_composition_portrait_and_review_advice(self) -> None:
        result = PhotoAnalysisResult(
            "A person was detected.",
            [Detection("Person", 0.95)],
            [],
            False,
        )

        recommendations = generate_recommendations(result, {"width": 800, "height": 1200})
        categories = {item.category for item in recommendations.items}
        texts = " ".join(item.text for item in recommendations.items)

        self.assertIn("composition", categories)
        self.assertIn("portrait-interaction", categories)
        self.assertIn("review", categories)
        self.assertIn("rule of thirds", texts)

    def test_detector_objects_infer_street_scene_and_rules(self) -> None:
        result = build_analysis_result(
            {},
            [{"class": "car", "confidence": 0.95}],
        )

        self.assertIn("street", {item.label.lower() for item in result.scene_attributes})
        categories = recommendation_categories(result, {"width": 1600, "height": 900})

        self.assertIn("lighting", categories)
        self.assertIn("alignment", categories)
        self.assertIn("composition", categories)
        self.assertIn("timing", categories)

    def test_kitchen_inference_produces_indoor_and_mixed_light_advice(self) -> None:
        result = build_analysis_result(
            {},
            [{"class": "oven", "confidence": 0.95}],
        )
        categories = recommendation_categories(result, {"width": 1000, "height": 1000})

        self.assertIn("lighting", categories)
        self.assertIn("alignment", categories)
        self.assertIn("composition", categories)
        lighting_text = " ".join(
            item.text
            for item in generate_recommendations(result, {"width": 1000, "height": 1000}).items
            if item.category == "lighting"
        )
        self.assertIn("light color", lighting_text)

    def test_optional_signals_enable_gated_recommendations(self) -> None:
        signals = AnalysisSignals(
            subject_position="left",
            dominant_color="blue",
            motion_blur=True,
            shallow_depth_of_field=True,
            time_of_day="midday",
            light_quality="hard",
        )
        result = PhotoAnalysisResult(
            "A person outdoors.",
            [Detection("Person", 0.95)],
            [Detection("street", 0.95)],
            False,
            signals=signals,
        )

        recommendations = generate_recommendations(result, {"width": 1600, "height": 900})
        categories = {item.category for item in recommendations.items}

        self.assertIn("color", categories)
        self.assertIn("camera-settings", categories)
        self.assertIn("timing", categories)
        self.assertIn("perspective", categories)
        self.assertTrue(any("golden-ratio" in item.text for item in recommendations.items))

    def test_missing_signals_do_not_create_technical_or_color_claims(self) -> None:
        result = PhotoAnalysisResult(
            "A car was detected.",
            [Detection("Car", 0.95)],
            [Detection("street", 0.95)],
            False,
        )
        categories = recommendation_categories(result, {"width": 1600, "height": 900})

        self.assertNotIn("camera-settings", categories)
        self.assertNotIn("color", categories)

    def test_uncertain_inferred_scene_sets_uncertain_output(self) -> None:
        result = build_analysis_result(
            {},
            [{"class": "car", "confidence": 0.60}],
        )

        recommendations = generate_recommendations(result, {"width": 1600, "height": 900})

        self.assertTrue(recommendations.uncertain)
        self.assertTrue(any(item.category == "uncertainty" for item in recommendations.items))

    def test_empty_analysis_returns_practice_tip(self) -> None:
        result = PhotoAnalysisResult("No useful detections.", [], [], True)

        recommendations = generate_recommendations(result, {})
        categories = {item.category for item in recommendations.items}

        self.assertIn("practice", categories)
        self.assertNotIn("review", categories)

    def test_alignment_actions_are_not_duplicated(self) -> None:
        result = PhotoAnalysisResult(
            "A street scene.",
            [],
            [Detection("street", 0.95)],
            False,
        )

        recommendations = generate_recommendations(result, {"width": 1600, "height": 900})
        alignment = [item for item in recommendations.items if item.category == "alignment"]

        self.assertEqual(len(alignment), 2)
        self.assertEqual(len({item.text for item in alignment}), 2)


if __name__ == "__main__":
    unittest.main()
