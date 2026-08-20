# Photography Recommendations

## User story
As a photographer, I want practical suggestions based on the image analysis, so I can improve future photographs.

## Scope
Turn a structured `PhotoAnalysisResult` and basic image metadata into explainable photography recommendations covering lighting, alignment, composition, perspective, timing, color, camera settings, portrait interaction, review/learning, and practice.

Scenes that the underlying vision model does not emit directly (for example `street`, `indoor`, or `kitchen`) may be inferred from the detected object labels so that the recommendations have enough signal to fire.

## Inputs
- The structured result from `001-photo-analysis-result.md`
- Image width and height

## Rules
- Recommendations must be suggestions, not claims about the photographer's intent or facts that the analysis does not establish.
- Recommendations must be based on detected subjects, detected scenes, measurable image metadata, or image-analysis signals defined by `PhotoAnalysisResult`.
- Scene labels may be inferred from object detections when the vision model does not provide scene tags directly.
- Use only signals actually present in the input. In particular, do not infer exposure, white balance, focus, depth of field, motion blur, facial expression, eye contact, a horizon, light direction, light softness, color palette, or subject position unless `PhotoAnalysisResult` explicitly supplies a corresponding measurement or detection.
- When an available measurement supports it, recommendations may address light quality or direction, subject clarity, background simplification, perspective, timing, color, and camera settings.
- Camera-setting recommendations must describe the creative trade-off (aperture/depth of field, shutter speed/motion, or ISO/noise) and must be conditional on a supplied exposure, motion, depth, or noise signal; they must not prescribe a numeric setting without metadata that supports it.
- Portrait-interaction recommendations must be conditional on a detected person and framed as future-session advice; they must not claim that the current subject was posed, uncomfortable, or unengaged.
- Timing recommendations must be conditional on a detected outdoor scene plus available time-, weather-, or light-related analysis. If those signals are unavailable, use a generic future-session suggestion rather than naming golden hour, blue hour, overcast, or midday as a property of the current image.
- Color recommendations must be conditional on an available color, white-balance, or mixed-light signal. Do not infer a palette or color cast from object labels alone.
- Photo-review and practice recommendations may be generic learning advice and do not require an image-analysis signal, but they must not claim a specific flaw in the current image.
- Uncertain detections must produce cautious wording and set `PhotographyRecommendations.uncertain` to `true` when any returned recommendation relies on an uncertain detection or inference.
- Do not recommend image edits automatically.
- Do not return duplicate recommendations. Recommendations with the same category and materially the same action should be merged.
- Return a useful generic tip when there is not enough information for a specific recommendation.

## Recommendation triggers

### Lighting
- A `street` scene (cars, traffic lights, benches, signs, etc.) produces an outdoor/street-light tip. If light direction or quality is measured, the tip may specifically suggest working with, repositioning relative to, or waiting for softer/direct light.
- An `indoor` scene (furniture, appliances, decor, etc.) produces an available-light tip.
- A `kitchen` scene (oven, sink, fridge, dishes, etc.) produces a tip about avoiding mixed-color artificial light.
- A detected bright-background, uneven-light, hard-light, backlight, or low-light signal may produce a suggestion about changing subject/camera position, reducing distracting bright areas, or choosing softer/more even light, provided that signal is part of `PhotoAnalysisResult`.
- A measured mixed-light or white-balance signal may produce a color-temperature recommendation; a `kitchen` inference alone supports only a cautious mixed-artificial-light tip.

### Alignment
- A landscape-oriented image, or any outdoor/street scene, produces a horizon-level recommendation. Word it as a check unless a horizon/tilt measurement is supplied.
- An architectural scene (`street`, `indoor`, strong vertical objects) produces a vertical-alignment recommendation. Word it as a check unless a vertical-line or perspective measurement is supplied.

### Composition rules
- A detected **person** or **animal** produces a rule-of-thirds / off-center placement recommendation.
- A `street` scene produces a leading-lines recommendation.
- A scene with natural framing opportunities (`potted plant`, architectural openings, etc.) produces a framing recommendation.
- Architectural or symmetrical scenes (`indoor`, `street`) produce a symmetry recommendation.
- A single, isolated main subject produces a negative-space recommendation.
- A strong off-center subject may also produce a golden-ratio recommendation, only when subject position is supplied by the analysis.
- A detected main subject plus a supplied clutter, competing-subject, edge-intersection, or distracting-bright-area signal may produce a subject-clarity or background-simplification recommendation.
- A person or animal with a supplied subject-size, crop, or edge-proximity measurement may produce a recommendation to get closer, leave intentional space, or avoid an awkward crop.

### Perspective
- A detected person, animal, building, architectural scene, or strong foreground/background depth cue may produce a future-session perspective recommendation: try eye level, a lower angle, a higher angle, a close-up, or a wider environmental view.
- A low-angle, high-angle, convergence, or perspective-distortion recommendation must be tied to a corresponding supplied measurement; otherwise phrase the advice as an option to try rather than a correction.

### Timing
- An outdoor/street scene with a supplied time-of-day, weather, or light-quality signal may produce a timing recommendation about revisiting at golden hour, blue hour, overcast conditions, or a different time of day.
- Without those signals, an outdoor/street scene may produce only generic future-session timing advice, such as comparing the scene at different times of day.

### Color
- A supplied dominant-color, color-contrast, saturation, white-balance, or mixed-light signal may produce a recommendation to simplify the palette, use a complementary/analogous relationship, preserve a strong accent color, or check color temperature.
- Do not produce a color recommendation solely because a person, animal, or scene label is detected.

### Camera settings
- A supplied shallow/deep depth-of-field signal may produce an aperture trade-off recommendation.
- A supplied motion, motion-blur, or action-subject signal may produce a shutter-speed trade-off recommendation.
- A supplied low-light, high-noise, or ISO signal may produce an ISO/exposure trade-off recommendation.
- If no relevant technical measurement exists, do not issue a camera-setting recommendation merely because a scene or subject is detected.

### Portrait interaction
- A detected **person** may produce a future-session portrait-interaction recommendation, such as offering a simple action, directing shoulder/eye line, or photographing between poses.
- Do not infer that the subject needs to smile, was uncomfortable, was posed, or made eye contact unless that is explicitly provided by the analysis.

### Photo review and learning
- Any non-empty analysis may produce a review recommendation: compare a small set of strongest and weakest images, then assess subject, light, composition, distractions, and mood.
- The review recommendation must be framed as a learning exercise, not as a diagnosis of the current image.

### Practice
- When there is not enough information for a specific recommendation, return a generic practice suggestion, such as making five distinct compositions of one subject, photographing the same subject under different light, limiting a session to one color/shape/line, or recreating a reference composition.

### Framing by orientation
- Portrait orientation can produce a vertical-framing recommendation.
- Landscape orientation can produce a horizontal-framing recommendation.

## Acceptance criteria
- A detected person or animal produces a composition recommendation.
- A `street` scene produces a lighting, leading-lines, and alignment recommendation.
- An `indoor` scene produces a lighting and alignment recommendation.
- A `kitchen` scene produces a cautious mixed-light recommendation.
- Landscape orientation or a street scene produces a horizon-level recommendation.
- Architectural or indoor scenes produce a vertical-alignment recommendation.
- A single isolated subject produces a negative-space recommendation.
- Portrait and landscape orientation can produce different framing recommendations.
- When light direction or quality is supplied, the result can suggest how to work with it; without that signal, it does not claim a direction or softness.
- A supplied clutter, competing-subject, edge-intersection, or distracting-bright-area signal can produce a subject-clarity or background-simplification recommendation.
- A detected person, animal, building, or architectural scene can produce a future-session perspective recommendation without claiming the current angle is wrong.
- A timing recommendation names a specific lighting condition only when time-, weather-, or light-related analysis supports it; otherwise it remains generic future-session advice.
- A color recommendation requires an available color, white-balance, saturation, or mixed-light signal.
- An aperture, shutter-speed, or ISO recommendation requires the corresponding depth, motion, exposure, low-light, noise, or ISO signal and describes a trade-off rather than inventing numeric settings.
- A detected person can produce a future-session portrait-interaction recommendation without asserting an unsupported expression, pose, or emotion.
- A non-empty analysis can return a photo-review/learning recommendation framed as a learning exercise.
- Empty analysis returns a generic recommendation instead of failing.
- Uncertain analysis is reflected in the recommendation result and uses cautious wording.
- No duplicate recommendations are returned.
- The output continues to conform exactly to the data contract below.

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
