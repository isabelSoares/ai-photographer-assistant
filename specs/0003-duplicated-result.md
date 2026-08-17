# Results Duplicate Verification

## User story

As a developer, I want to verify `results.json` for duplicate image results, so that the analysis history remains reliable.

## Scope

Create a command-line verifier at `scripts/verify_results.py`.

## Inputs

- A JSON array stored in `results.json`
- Each record must contain `image_filename`

## Rules

- The results file must contain valid JSON.
- The root JSON value must be an array.
- Each record must contain a non-empty `image_filename`.
- Records with the same `image_filename` are duplicates.
- Keep only the first occurrence.
- The verifier must not modify `results.json`.
- Duplicate records must be reported with their indexes.
- Save the cleaned results in `cleaned_results.json`.
- Show statistics such as `duplicates_removed` and `total_records` in `cleaned_results.json`.

## Expected behavior

When no duplicates exist:

```text
Results validation passed.
Records checked: 3
Duplicates found: 0
```

When duplicates exist:
```text
Duplicate images found:
- test.jpg: records 2, 5
```

## Exit codes:
- 0: validation passed
- 1: duplicates found
- 2: invalid or missing results file

## Acceptance criteria:
- Invalid JSON causes exit code 2.
- A missing image_filename causes exit code 2.
- Duplicate filenames cause exit code 1.
- Unique filenames cause exit code 0.
- The original results file is not changed.
- The first record for each filename is kept in `cleaned_results.json`.
- `cleaned_results.json` contains `total_records`, `duplicates_removed`, and `unique_records`.

## Data contract
```json
{
  "module": "src/generated/results_validation_contract.py",
  "models": [
    {
      "name": "DuplicateGroup",
      "fields": [
        {"name": "image_filename", "type": "str"},
        {"name": "record_indexes", "type": "list[int]"}
      ]
    },
    {
      "name": "ValidationStatistics",
      "fields": [
        {"name": "total_records", "type": "int"},
        {"name": "duplicates_removed", "type": "int"},
        {"name": "unique_records", "type": "int"}
      ]
    }
  ]
}
```
