# Surface perturbation diff

Same logical task run 5 times: json_baseline, json_reordered, csv_same_data, csv_reordered, json_alt_filename (same content as baseline, different run label).

## Outputs (results.json records)

- All runs: 2 records, keys `['name', 'count']` after normalize_keys.
- **Real difference — format**: JSON runs have `count` as int (1, 2); CSV runs have `count` as str ("1", "2"). So CSV vs JSON changes value types.
- **Real difference — order**: json_reordered and csv_reordered have records in order (b,2)/(b,"2") then (a,1)/(a,"1"); baseline and csv_same_data have (a,1) then (b,2). Order is preserved from input.
- **Noise**: json_alt_filename vs json_baseline: same content, same output; file name / run label has no effect on records.

## Traces (trace.jsonl, ts stripped)

- All 5 runs: 1 event each, same shape (`keys_normalized`, source `ingestion.normalize_record_keys`, record_count 2). Only `ts` differs.
- **Noise**: Format, record order, and file name are not logged; trace cannot distinguish any of the perturbations.

## Summary

| Perturbation     | Output changes?     | Trace changes? |
|------------------|---------------------|----------------|
| CSV vs JSON      | Yes (count int vs str) | No          |
| Record order     | Yes (order preserved)  | No          |
| File name / label| No                  | No             |

Real behavioral differences: format (type of numeric fields), order (preserved). Noise: file name; and in traces, everything except ts is identical across runs.
