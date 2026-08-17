# Results Verification Decisions

## Context

The application stores one analysis result per processed image in `results.json`.
Batch runs append results, so the same image can appear more than once.

## Decisions

### Duplicate identity

Two records are duplicates when their `image_filename` values are equal. The
filename is the stable identity currently available in the result contract.
Filename matching is exact and case-sensitive.

### Cleanup behavior

The first occurrence is retained because it represents the earliest result in the
history. Later occurrences are removed from `cleaned_results.json`.
The source `results.json` is never modified by the verifier.

### Output format

`results.json` remains the source history. `cleaned_results.json` is a JSON object
with `statistics` and `records`, making cleanup metrics available without changing
the source format.

### Exit codes

- `0`: valid input with no duplicates
- `1`: valid input with duplicates; cleaned output is still produced
- `2`: missing, invalid, or structurally invalid input, or failure to write output

### Implementation boundary

The Markdown specification generates the `DuplicateGroup` and
`ValidationStatistics` data contracts. The command-line verifier remains hand-written
because the current generator produces models, not complete command-line programs.

## Consequences

- Re-running the batch processor can create duplicate history records.
- The verifier is deterministic and does not require an AI model.
- If filenames cease to be unique identifiers, the spec and this decision must be
  updated together, potentially to use a content hash or image ID.
