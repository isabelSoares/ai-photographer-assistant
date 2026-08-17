# ai-photographer-assistant
AI photographer Assistant that helps you to improve your photography skills.

## Spec-driven development

The `specs/` directory is the source of truth. Markdown keeps the intent readable for people; a fenced JSON `Data contract` block makes the parts needed by code unambiguous. `scripts/spec.py` is the bridge:

```text
Markdown spec -> check -> generated Python dataclasses -> application code/tests
```

Run the complete workflow from the repository root:

```bash
python scripts/spec.py all
```

Use `check` when reviewing a specification and `generate` after changing its
contract. Generated files live under `src/generated/` and must not be edited by hand. The implementation in `src/photo_analysis.py` consumes the generated
`PhotoAnalysisResult`, keeping the spec, contract, and runtime output connected.

Photography advice is defined separately in
`specs/002-photography-recommendations.md` and implemented by `src/recommendations.py`.
This keeps detected facts separate from creative
suggestions.

Markdown itself does not execute or generate Python. The connection is an explicit tool: it locates the JSON contract, validates it, and renders the declared models
as Python dataclasses. An AI assistant can use the same spec to propose behavior, but the contract and `spec check` provide deterministic, reviewable boundaries.

## Verify result history

Validate duplicate image results and generate a cleaned copy:

```bash
.venv/bin/python scripts/verify_results.py
```

The command checks `results.json`, keeps the first result for each filename, and
writes `cleaned_results.json`. It returns `0` for valid unique results, `1` when
duplicates are found, and `2` for invalid input. The source history is never
modified. The decisions are documented in
`docs/decisions/0001-results-verification.md`.
