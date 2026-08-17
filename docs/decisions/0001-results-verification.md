# ADR-0001: Results Verification and Cleanup

## Status

Accepted

## Date

2026-08-17

## Context

`src/main.py` processes all images in `converted_photos/` and appends one result record per image to `results.json`. Re-running the batch intentionally preserves
history, but it can add another record for the same image. Consumers need a safe way to identify and remove duplicate history records without destroying the source
data.

The result contract currently identifies an image by `image_filename`. There is no
persisted image ID or content hash.

## Decision

Implement `scripts/verify_results.py` as a deterministic command-line verifier.
The verifier reads `results.json`, validates its structure, reports duplicates, and writes a separate `cleaned_results.json`.

## Duplicate Identity

Two records are duplicates when their `image_filename` values are equal. Matching
is exact and case-sensitive. For example, `photo.jpg` and `Photo.jpg` are currently different identifiers.

The verifier reports all indexes for a duplicated filename. Indexes are one-based to match the way people read the JSON records in the file.

## Cleanup Policy

The first occurrence of a filename is retained. Later occurrences are removed from the cleaned output because the first record is the earliest history entry.

The source `results.json` is never modified. `cleaned_results.json` contains:

```json
{
    "statistics": {
        "total_records": 3,
        "duplicates_removed": 1,
        "unique_records": 2
    },
    "records": []
}
```

Cleaning is performed for both unique and duplicate input. If duplicates are found, the cleaned file is still written before the command exits with code `1`.

## Validation Rules

The input is invalid when:

- The file does not exist
- The file is not valid JSON
- The root value is not an array
- A record is not an object
- A record has a missing, non-string, or blank `image_filename`
- The cleaned output cannot be written

Invalid input returns exit code `2` and must not produce a misleading successful validation message.

## Exit Codes

- `0`: valid results and no duplicates
- `1`: valid results with one or more duplicates; cleaned output was produced
- `2`: missing, invalid, or structurally invalid input, or output failure

## Alternatives Considered

### Overwrite `results.json`

Rejected because cleanup should be reversible and must not destroy the original analysis history.

### Append duplicate reports to the source file

Rejected because reports would mix operational metadata with application result records and make the source harder to consume as JSON.

### Use JSON Lines for the cleaned output

Rejected for the cleaned artifact because consumers expect a normal JSON document.
The historical `results.json` may have been written as line-delimited records in earlier versions, but the current batch writer stores a JSON array.

### Deduplicate by image content hash

Deferred. A content hash would identify renamed copies of the same image, but it
requires hashing every file and adding a hash to the result contract. Revisit this
when filename identity is no longer sufficient.

## Implementation Boundary

The Markdown specification generates `DuplicateGroup` and `ValidationStatistics` dataclasses. The command-line verifier remains hand-written because the current generator produces models, not complete command-line programs.

## Testing

Acceptance tests cover:

- Valid unique results
- Duplicate indexes and first-record retention
- Invalid JSON
- Missing results file
- Non-array root values
- Non-object records
- Blank filenames
- Correct cleanup statistics
- Preservation of the original source file

## Consequences

- Batch reruns can create duplicate history and should be followed by verification when a clean dataset is needed.
- The verifier is deterministic, fast, and does not require YOLO or an AI model.
- `cleaned_results.json` is derived output and can be regenerated at any time.
- If filenames stop being reliable identifiers, this ADR and the related Markdown spec must be updated together, potentially to use an image ID or content hash.
