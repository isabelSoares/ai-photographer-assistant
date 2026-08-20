from generated.photo_analysis_contract import AnalysisSignals, PhotoAnalysisResult
from generated.recommendations_contract import PhotographyRecommendations, Recommendation


ANIMAL_LABELS = {
    "bear",
    "bird",
    "cat",
    "cow",
    "dog",
    "elephant",
    "giraffe",
    "horse",
    "sheep",
    "zebra",
}


def generate_recommendations(
    result: PhotoAnalysisResult,
    image_info: dict,
) -> PhotographyRecommendations:
    """Generate signal-aware, explainable photography suggestions."""
    recommendations: list[Recommendation] = []
    recommendation_keys: set[tuple[str, str]] = set()
    subjects = {item.label.lower() for item in result.subjects}
    scenes = {item.label.lower() for item in result.scene_attributes}
    signals = getattr(result, "signals", None) or AnalysisSignals()
    analysis_uncertain = result.uncertain or any(
        item.possible for item in [*result.subjects, *result.scene_attributes]
    )

    def add(text: str, category: str, reason: str, action: str) -> None:
        key = (category, action)
        if key not in recommendation_keys:
            recommendations.append(Recommendation(text, category, reason))
            recommendation_keys.add(key)

    people_or_animals = bool(subjects & ({"person"} | ANIMAL_LABELS))
    street_scene = bool(scenes & {"street", "outdoor"})
    indoor_scene = bool(scenes & {"indoor", "kitchen"})
    architectural_scene = bool(scenes & {"street", "indoor", "kitchen", "city"})

    # Lighting recommendations use street as the outdoor-light proxy.
    if street_scene:
        if signals.light_quality or signals.backlight or signals.hard_light:
            add(
                "Try changing your position relative to the light or wait for softer light to reduce harsh or backlit areas.",
                "lighting",
                "The analysis supplied a light-quality or backlight signal for a street scene.",
                "directional-light",
            )
        else:
            add(
                "Look for soft, directional natural light and consider changing position to shape the subject.",
                "lighting",
                "A street scene was detected; it is being used as the outdoor-light proxy.",
                "natural-light",
            )
    if indoor_scene:
        add(
            "Place the subject near available window light when possible, and avoid mixing strongly different light colors.",
            "lighting",
            "An indoor scene was detected.",
            "available-light",
        )
    if "kitchen" in scenes or signals.mixed_light:
        add(
            "Use one dominant light color when possible to keep the scene's color temperature consistent.",
            "lighting",
            "A kitchen or mixed-light signal was detected.",
            "mixed-light",
        )
    if signals.bright_background or signals.distracting_bright_area:
        add(
            "Try repositioning the camera or subject so bright background areas do not compete for attention.",
            "lighting",
            "A bright-background signal was supplied by the analysis.",
            "bright-background",
        )
    if signals.uneven_light or signals.low_light:
        add(
            "Look for a more even light source or move the subject toward the available light for clearer detail.",
            "lighting",
            "The analysis supplied an uneven- or low-light signal.",
            "even-light",
        )

    # Alignment recommendations remain checks unless the analysis measured a problem.
    width = image_info.get("width")
    height = image_info.get("height")
    landscape = isinstance(width, int) and isinstance(height, int) and width > height
    portrait = isinstance(width, int) and isinstance(height, int) and height > width
    if landscape or street_scene:
        horizon_text = (
            "The horizon appears tilted; level it during the next composition."
            if signals.horizon_tilt
            else "Check that the horizon is level when composing the next frame."
        )
        add(horizon_text, "alignment", "The image is landscape-oriented or a street scene was detected.", "horizon")
    if architectural_scene:
        vertical_text = (
            "Vertical lines appear to converge; try a more level camera position or correct the perspective in-camera."
            if signals.vertical_line_issue or signals.perspective_distortion
            else "Check that architectural vertical lines stay straight when composing the next frame."
        )
        add(vertical_text, "alignment", "An architectural, indoor, or street scene was detected.", "vertical-lines")

    # Composition rules.
    if people_or_animals:
        subject = "person" if "person" in subjects else "main subject"
        add(
            f"Try placing the {subject} slightly off-center using the rule of thirds to create a more dynamic composition.",
            "composition",
            "A person or animal was detected as a main subject.",
            "rule-of-thirds",
        )
    if "street" in scenes:
        add(
            "Use roads, kerbs, or repeated street elements as leading lines toward the main subject.",
            "composition",
            "A street scene was detected.",
            "leading-lines",
        )
    if "potted plant" in subjects or signals.depth_cue or signals.natural_framing:
        add(
            "Use a nearby foreground element as a frame around the subject while keeping the subject clear.",
            "composition",
            "A natural-framing opportunity or depth cue was supplied.",
            "natural-framing",
        )
    if architectural_scene:
        add(
            "Look for repeated shapes or balanced sides if you want to emphasize symmetry.",
            "composition",
            "An indoor, street, city, or kitchen scene was detected.",
            "symmetry",
        )
    single_subject = signals.isolated_subject or signals.subject_count == 1 or len(subjects) == 1
    if single_subject:
        add(
            "Leave intentional negative space around the single subject to make the frame feel less crowded.",
            "composition",
            "One main subject was detected without evidence of competing subjects.",
            "negative-space",
        )
    if signals.subject_position:
        add(
            "Compare a rule-of-thirds placement with a golden-ratio placement and choose the balance that best supports the subject.",
            "composition",
            "The analysis supplied the subject position needed for this comparison.",
            "golden-ratio",
        )
    if signals.clutter or signals.competing_subjects or signals.edge_intersection:
        add(
            "Simplify the background or change your position so the main subject is easier to read.",
            "composition",
            "The analysis supplied a clutter, competing-subject, or edge-intersection signal.",
            "subject-clarity",
        )
    if people_or_animals and (signals.subject_size or signals.crop or signals.edge_proximity):
        add(
            "Check the subject's space at the frame edges; try getting closer or leaving intentional breathing room in the next frame.",
            "composition",
            "The analysis supplied subject-size, crop, or edge-proximity information.",
            "edge-space",
        )

    # Perspective is future-session advice unless a measured issue is supplied.
    if people_or_animals or "building" in subjects or architectural_scene or signals.depth_cue:
        add(
            "For a future frame, compare eye-level, lower, and higher viewpoints to change the subject's relationship with its surroundings.",
            "perspective",
            "A subject, architectural scene, or depth cue supports trying alternative viewpoints.",
            "viewpoint",
        )
    if signals.convergence or signals.perspective_distortion:
        add(
            "Try stepping back or changing camera height to manage converging lines and perspective distortion.",
            "perspective",
            "The analysis supplied a convergence or perspective-distortion signal.",
            "distortion",
        )

    # Timing names a particular condition only when it is supplied.
    if street_scene:
        if signals.time_of_day or signals.weather or signals.light_quality:
            add(
                "Consider revisiting at a different time or under different weather to compare how the light changes the scene.",
                "timing",
                "Time, weather, or light-quality information was supplied for a street scene.",
                "specific-timing",
            )
        else:
            add(
                "Photograph the scene at two different times of day and compare the direction, contrast, and mood of the light.",
                "timing",
                "A street scene was detected, but no current time or weather signal was supplied.",
                "compare-timing",
            )

    # Color and camera settings require technical signals.
    if signals.dominant_color or signals.color_contrast or signals.saturation:
        add(
            "Use the detected color relationships deliberately: simplify competing colors or preserve one strong accent.",
            "color",
            "The analysis supplied color information.",
            "color-relationships",
        )
    if signals.white_balance or signals.mixed_light:
        add(
            "Check the color temperature and keep the dominant light source consistent where possible.",
            "color",
            "The analysis supplied white-balance or mixed-light information.",
            "color-temperature",
        )
    if signals.shallow_depth_of_field or signals.deep_depth_of_field:
        add(
            "Choose a wider aperture for more background separation or a narrower aperture when you need more of the scene sharp.",
            "camera-settings",
            "The analysis supplied a depth-of-field signal.",
            "aperture-depth",
        )
    if signals.motion or signals.motion_blur or signals.action_subject:
        add(
            "Use a faster shutter speed to reduce motion blur, or a slower one deliberately when motion should be visible.",
            "camera-settings",
            "The analysis supplied a motion or action signal.",
            "shutter-motion",
        )
    if signals.low_light or signals.high_noise or signals.iso is not None or signals.exposure:
        add(
            "Balance a higher ISO for a brighter exposure against additional noise, and use the cleanest exposure the scene allows.",
            "camera-settings",
            "The analysis supplied a low-light, noise, ISO, or exposure signal.",
            "iso-noise",
        )

    if "person" in subjects:
        add(
            "For a future portrait, offer a simple action or direction and photograph between poses for more natural moments.",
            "portrait-interaction",
            "A person was detected; this is future-session advice rather than a claim about the current pose.",
            "between-poses",
        )

    if subjects or scenes:
        add(
            "Review a small set of your strongest and weakest frames, comparing subject, light, composition, distractions, and mood as a learning exercise.",
            "review",
            "The analysis contains information that can support a future review exercise.",
            "review-set",
        )
    else:
        add(
            "Practice by making five distinct compositions of one subject under different light.",
            "practice",
            "There is not enough reliable information for a specific recommendation.",
            "five-compositions",
        )

    if portrait:
        add(
            "Use the vertical frame to emphasize height and the main subject.",
            "framing",
            "The image is portrait-oriented.",
            "vertical-frame",
        )
    elif landscape:
        add(
            "Use the horizontal frame to include context around the main subject.",
            "framing",
            "The image is landscape-oriented.",
            "horizontal-frame",
        )

    if analysis_uncertain:
        add(
            "Some suggestions are tentative because parts of the analysis are uncertain.",
            "uncertainty",
            "One or more detections or inferences were uncertain.",
            "uncertain-analysis",
        )

    return PhotographyRecommendations(recommendations, analysis_uncertain)
