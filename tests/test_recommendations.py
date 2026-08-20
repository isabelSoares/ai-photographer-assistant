import sys
import re
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
    def test_recommendations_have_explainable_non_empty_fields(self) -> None:
        result = PhotoAnalysisResult(
            "A person was detected.",
            [Detection("Person", 0.95)],
            [],
            False,
        )

        recommendations = generate_recommendations(result, {"width": 800, "height": 1200})

        self.assertTrue(recommendations.items)
        for item in recommendations.items:
            self.assertTrue(item.text.strip())
            self.assertTrue(item.category.strip())
            self.assertTrue(item.reason.strip())

    def test_actionable_recommendations_use_action_language(self) -> None:
        result = PhotoAnalysisResult(
            "A person outdoors.",
            [Detection("Person", 0.95)],
            [Detection("street", 0.95)],
            False,
        )
        recommendations = generate_recommendations(result, {"width": 1600, "height": 900})
        action_words = re.compile(
            r"\b(try|look|use|check|place|leave|review|practice|consider|balance|choose|offer|photograph|compare)\b",
            re.IGNORECASE,
        )

        for item in recommendations.items:
            if item.category == "uncertainty":
                continue
            self.assertRegex(item.text, action_words, msg=item.text)

    def test_person_advice_does_not_invent_emotion_or_pose(self) -> None:
        result = PhotoAnalysisResult(
            "A person was detected.",
            [Detection("Person", 0.95)],
            [],
            False,
        )

        text = " ".join(item.text.lower() for item in generate_recommendations(result, {}).items)

        for unsupported_claim in ("uncomfortable", "unengaged", "was posed", "eye contact"):
            self.assertNotIn(unsupported_claim, text)

    def test_missing_light_signals_do_not_claim_specific_light_conditions(self) -> None:
        result = PhotoAnalysisResult(
            "A car was detected.",
            [Detection("Car", 0.95)],
            [Detection("street", 0.95)],
            False,
        )

        text = " ".join(item.text.lower() for item in generate_recommendations(result, {}).items)

        for unsupported_condition in ("hard light", "backlit", "golden hour", "blue hour", "overcast", "midday"):
            self.assertNotIn(unsupported_condition, text)

    def test_camera_advice_requires_signal_and_explains_tradeoff(self) -> None:
        without_signal = PhotoAnalysisResult(
            "A person was detected.",
            [Detection("Person", 0.95)],
            [],
            False,
        )
        without_camera_advice = generate_recommendations(without_signal, {})
        self.assertNotIn("camera-settings", {item.category for item in without_camera_advice.items})

        with_signal = PhotoAnalysisResult(
            "A person was detected in low light.",
            [Detection("Person", 0.95)],
            [],
            False,
            signals=AnalysisSignals(low_light=True, high_noise=True),
        )
        camera_advice = [
            item.text
            for item in generate_recommendations(with_signal, {}).items
            if item.category == "camera-settings"
        ]
        self.assertTrue(camera_advice)
        self.assertIn("ISO", camera_advice[0])
        self.assertIn("noise", camera_advice[0].lower())
        self.assertNotRegex(camera_advice[0], r"\b\d{3,4}\b")

    def test_uncertain_recommendations_are_explicitly_cautious(self) -> None:
        result = PhotoAnalysisResult(
            "A possible person was detected.",
            [Detection("Person", 0.60, possible=True)],
            [],
            False,
        )

        recommendations = generate_recommendations(result, {})
        uncertainty_items = [item for item in recommendations.items if item.category == "uncertainty"]

        self.assertTrue(recommendations.uncertain)
        self.assertEqual(len(uncertainty_items), 1)
        self.assertIn("tentative", uncertainty_items[0].text.lower())

    def test_same_category_does_not_repeat_identical_advice(self) -> None:
        result = PhotoAnalysisResult(
            "A street scene.",
            [],
            [Detection("street", 0.95)],
            False,
        )

        recommendations = generate_recommendations(result, {"width": 1600, "height": 900})
        texts_by_category: dict[str, list[str]] = {}
        for item in recommendations.items:
            texts_by_category.setdefault(item.category, []).append(item.text)

        for category, texts in texts_by_category.items():
            self.assertEqual(len(texts), len(set(texts)), category)

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
