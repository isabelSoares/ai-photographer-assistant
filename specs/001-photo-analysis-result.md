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
5. A notice when the analysis is uncertain or unavailable

## Rules
- Show only detections above the agreed confidence threshold.
- Use plain language instead of raw model labels where possible.
- Label low-confidence conclusions as possible, rather than definite.
- Do not invent details missing from the detection output.
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
- The result contains a summary, subjects, scene attributes, and uncertainty information.
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
    {"name": "PhotoAnalysisResult", "fields": [
      {"name": "summary", "type": "str"},
      {"name": "subjects", "type": "list[Detection]"},
      {"name": "scene_attributes", "type": "list[Detection]"},
      {"name": "uncertain", "type": "bool"},
      {"name": "notice", "type": "str | None", "default": "None"}
    ]}
  ]
}
```
