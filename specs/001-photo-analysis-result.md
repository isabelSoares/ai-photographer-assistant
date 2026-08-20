# Photo Analysis Result

## User story
As a photographer, I want to upload a photo and receive a clear summary of what the assistant detected, so I can understand the image before acting on suggestions.

## Scope
Transform raw image-detection output into a structured analysis result.

## Inputs
- One supported image file
- Detection output from the chosen vision model or image-analysis service

## Expected result
The assistant displays:
1. A short image summary
2. Detected subjects or objects
3. Relevant scene attributes, when available
4. Detection confidence
5. Measurable analysis signals, when available
6. A notice when the analysis is uncertain or unavailable

## Rules
- Show only detections above the agreed confidence threshold.
- Use plain language instead of raw model labels where possible.
- Label low-confidence conclusions as possible, rather than definite.
- Do not invent details missing from the detection output.
- Preserve measurable signals such as lighting, color, motion, depth, perspective, and subject-position findings when the analysis service supplies them.
- If no useful detection is returned, show a helpful fallback message.

## Example

### Given
The detector returns:
- `person`, confidence 0.96
- `dog`, confidence 0.88
- `outdoor`, confidence 0.72

### Then
The user sees:
- Summary: “This photo appears to show a person and a dog outdoors.”
- Detected subjects: Person (96%), Dog (88%)
- Scene: Outdoor (72%)

### Fallback example
If the detector returns no usable labels:
- “I couldn’t confidently identify the main subjects in this image. Try a clearer or better-lit photo.”

## Acceptance criteria
- Detections below the configured confidence threshold are excluded.
- Labels with confidence below 75% are marked as possible.
- The result contains a summary, subjects, scene attributes, uncertainty information, and available analysis signals.
- When no usable detections exist, the result contains the fallback notice above.

## Data contract
The JSON block below is machine-readable. Run `python scripts/spec.py generate` after changing it.

```json
{
  "module": "src/generated/photo_analysis_contract.py",
  "models": [
    {"name": "Detection", "fields": [
      {"name": "label", "type": "str"},
      {"name": "confidence", "type": "float"},
      {"name": "possible", "type": "bool", "default": "False"}
    ]},
    {"name": "AnalysisSignals", "fields": [
      {"name": "bright_background", "type": "bool", "default": "False"},
      {"name": "uneven_light", "type": "bool", "default": "False"},
      {"name": "hard_light", "type": "bool", "default": "False"},
      {"name": "backlight", "type": "bool", "default": "False"},
      {"name": "low_light", "type": "bool", "default": "False"},
      {"name": "mixed_light", "type": "bool", "default": "False"},
      {"name": "white_balance", "type": "str | None", "default": "None"},
      {"name": "dominant_color", "type": "str | None", "default": "None"},
      {"name": "color_contrast", "type": "str | None", "default": "None"},
      {"name": "saturation", "type": "str | None", "default": "None"},
      {"name": "shallow_depth_of_field", "type": "bool", "default": "False"},
      {"name": "deep_depth_of_field", "type": "bool", "default": "False"},
      {"name": "motion", "type": "bool", "default": "False"},
      {"name": "motion_blur", "type": "bool", "default": "False"},
      {"name": "action_subject", "type": "bool", "default": "False"},
      {"name": "high_noise", "type": "bool", "default": "False"},
      {"name": "iso", "type": "int | None", "default": "None"},
      {"name": "exposure", "type": "str | None", "default": "None"},
      {"name": "subject_count", "type": "int | None", "default": "None"},
      {"name": "isolated_subject", "type": "bool", "default": "False"},
      {"name": "subject_position", "type": "str | None", "default": "None"},
      {"name": "subject_size", "type": "str | None", "default": "None"},
      {"name": "crop", "type": "str | None", "default": "None"},
      {"name": "edge_proximity", "type": "str | None", "default": "None"},
      {"name": "clutter", "type": "bool", "default": "False"},
      {"name": "competing_subjects", "type": "bool", "default": "False"},
      {"name": "edge_intersection", "type": "bool", "default": "False"},
      {"name": "distracting_bright_area", "type": "bool", "default": "False"},
      {"name": "depth_cue", "type": "bool", "default": "False"},
      {"name": "natural_framing", "type": "bool", "default": "False"},
      {"name": "low_angle", "type": "bool", "default": "False"},
      {"name": "high_angle", "type": "bool", "default": "False"},
      {"name": "convergence", "type": "bool", "default": "False"},
      {"name": "perspective_distortion", "type": "bool", "default": "False"},
      {"name": "time_of_day", "type": "str | None", "default": "None"},
      {"name": "weather", "type": "str | None", "default": "None"},
      {"name": "light_quality", "type": "str | None", "default": "None"},
      {"name": "horizon_tilt", "type": "bool", "default": "False"},
      {"name": "vertical_line_issue", "type": "bool", "default": "False"}
    ]},
    {"name": "PhotoAnalysisResult", "fields": [
      {"name": "summary", "type": "str"},
      {"name": "subjects", "type": "list[Detection]"},
      {"name": "scene_attributes", "type": "list[Detection]"},
      {"name": "uncertain", "type": "bool"},
      {"name": "notice", "type": "str | None", "default": "None"},
      {"name": "signals", "type": "AnalysisSignals | None", "default": "None"}
    ]}
  ]
}
```
