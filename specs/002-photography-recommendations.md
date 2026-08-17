# Photography Recommendations

## User story
As a photographer, I want practical suggestions based on the image analysis, so I can improve future photographs.

## Scope
Turn a structured `PhotoAnalysisResult` and basic image metadata into explainable photography recommendations.

## Inputs
- The structured result from `001-photo-analysis-result.md`
- Image width and height

## Rules
- Recommendations must be suggestions, not claims about the photographer's intent.
- Recommendations must be based on detected subjects, detected scenes, or measurable image metadata.
- Uncertain detections must produce cautious wording.
- Do not recommend image edits automatically.
- Do not return duplicate recommendations.
- Return a useful generic tip when there is not enough information for a specific recommendation.

## Acceptance criteria
- A detected person produces a composition recommendation.
- An outdoor scene produces a lighting recommendation.
- Portrait and landscape orientation can produce different framing recommendations.
- Uncertain analysis is reflected in the recommendation result.
- Empty analysis returns a generic recommendation instead of failing.

## Data contract
```json
{
  "module": "src/generated/recommendations_contract.py",
  "models": [
    {"name": "Recommendation", "fields": [
      {"name": "text", "type": "str"},
      {"name": "category", "type": "str"},
      {"name": "reason", "type": "str"}
    ]},
    {"name": "PhotographyRecommendations", "fields": [
      {"name": "items", "type": "list[Recommendation]"},
      {"name": "uncertain", "type": "bool"}
    ]}
  ]
}
```
