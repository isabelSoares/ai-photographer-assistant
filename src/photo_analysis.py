from generated.photo_analysis_contract import Detection, PhotoAnalysisResult

SCENE_LABELS = {"outdoor", "indoor", "beach", "mountain", "city", "kitchen", "street"}
FALLBACK_NOTICE = (
    "I couldn't confidently identify the main subjects in this image. "
    "Try a clearer or better-lit photo."
)


def build_analysis_result(
    image_info: dict,
    detections: list[dict],
    threshold: float = 0.5,
) -> PhotoAnalysisResult:
    """Convert raw detector labels into the result defined by spec 001."""
    del image_info  # Reserved for future summary details; do not invent any now.
    usable = [item for item in detections if float(item.get("confidence", 0)) >= threshold]
    parsed = [
        Detection(
            label=str(item["class"]).replace("_", " ").title(),
            confidence=float(item["confidence"]),
            possible=float(item["confidence"]) < 0.75,
        )
        for item in usable
        if item.get("class")
    ]
    subjects = [item for item in parsed if item.label.lower() not in SCENE_LABELS]
    scene = [item for item in parsed if item.label.lower() in SCENE_LABELS]
    if not parsed:
        return PhotoAnalysisResult(FALLBACK_NOTICE, [], [], True, FALLBACK_NOTICE)
    subject_labels = [f"a {item.label.lower()}" for item in subjects]
    summary = "This photo appears to show " + _join(subject_labels or ["a scene"])
    if scene:
        scene_label = scene[0].label.lower()
        summary += " outdoors" if scene_label == "outdoor" else f" in a {scene_label} setting"
    summary += "."
    uncertain = any(item.possible for item in parsed)
    return PhotoAnalysisResult(summary, subjects, scene, uncertain, None)


def _join(items: list[str]) -> str:
    if len(items) == 1:
        return items[0]
    if len(items) == 2:
        return f"{items[0]} and {items[1]}"
    return ", ".join(items[:-1]) + f", and {items[-1]}"
