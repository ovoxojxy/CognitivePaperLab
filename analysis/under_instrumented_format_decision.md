# Under-instrumented decision: input format (JSON vs CSV)

## Decision

In `ingestion.ingest()`, the first branch is:

```python
if format == "json":
    records = parse_json(raw)
elif format == "csv":
    records = parse_csv(raw)
```

**We do not emit any trace event that records which branch was taken.** The pipeline never logs `format` or "parsed_as" or equivalent.

## Why it's plausible to explain what happened

After a run, someone could reasonably say "we ingested JSON" or "we ingested CSV" based on how they invoked the CLI or script. The outcome (records) can look the same if both inputs represent the same data and `normalize_keys=True`. So explaining the run as "we parsed JSON" or "we parsed CSV" is plausible.

## What is genuinely unknowable from traces

From `trace.jsonl` alone we **cannot** determine whether the input was parsed as JSON or as CSV. There is no event that includes `format`, `parser`, or equivalent. The only ingestion-related event we emit is `keys_normalized` from `ingestion.normalize_record_keys` when `normalize_keys=True`. So for two runs that use the same config but different formats (one JSON, one CSV), the trace events are indistinguishable with respect to format.

## Experiment

Script: `experiments/run_format_observability.py`

- Runs the same logical input twice: once as JSON, once as CSV.
- Both use `normalize_keys=True`, storage=MemoryStorage.
- Writes each run to `runs/<timestamp>_format_observability_as_json` and `runs/<timestamp>_format_observability_as_csv`.
- Saves `meta.json` in each run dir with `format` so we can compare: the **trace.jsonl** in both runs contains only `keys_normalized` (same event shape); the **format** is recorded only in `meta.json`, not in the trace.

Conclusion: the **format decision is under-instrumented**. We do not fix it here; we only document the gap.
