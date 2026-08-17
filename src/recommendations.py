from generated.recommendations_contract import PhotographyRecommendations, Recommendation
from generated.photo_analysis_contract import PhotoAnalysisResult


def generate_recommendations(
    result: PhotoAnalysisResult,
    image_info: dict,
) -> PhotographyRecommendations:
    """Generate explainable photography suggestions from structured image facts."""
    recommendations: list[Recommendation] = []
    subjects = {item.label.lower() for item in result.subjects}
    scenes = {item.label.lower() for item in result.scene_attributes}

    if "person" in subjects:
        recommendations.append(
            Recommendation(
                "Try placing the person slightly off-center to create a more dynamic composition.",
                "composition",
                "A person was detected as a main subject.",
            )
        )
    if "outdoor" in scenes:
        recommendations.append(
            Recommendation(
                "Check the direction and harshness of the sunlight on the subject.",
                "lighting",
                "An outdoor scene was detected.",
            )
        )

    width = image_info.get("width")
    height = image_info.get("height")
    if isinstance(width, int) and isinstance(height, int) and width > 0 and height > 0:
        if height > width:
            recommendations.append(
                Recommendation(
                    "Use the vertical frame to emphasize height and the main subject.",
                    "framing",
                    "The image is portrait-oriented.",
                )
            )
        elif width > height:
            recommendations.append(
                Recommendation(
                    "Use the horizontal frame to include context around the main subject.",
                    "framing",
                    "The image is landscape-oriented.",
                )
            )

    if not recommendations:
        recommendations.append(
            Recommendation(
                "Try a clear, well-lit composition with one obvious point of interest.",
                "general",
                "There is not enough reliable information for a more specific suggestion.",
            )
        )

    if result.uncertain:
        recommendations.append(
            Recommendation(
                "Some suggestions are tentative because parts of the analysis are uncertain.",
                "uncertainty",
                "One or more detections were below the high-confidence level.",
            )
        )

    return PhotographyRecommendations(recommendations, result.uncertain)
