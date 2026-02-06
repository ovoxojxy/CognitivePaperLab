#!/usr/bin/env python3
"""Single-run introspector: summarizes a run folder.
Outputs: schema/types per field, record count, ordering signature,
trace inventory, missing trace fields.
"""

import json
import sys
from pathlib import Path
from collections import defaultdict


def infer_type(val):
    if val is None:
        return "null"
    if isinstance(val, bool):
        return "boolean"
    if isinstance(val, int):
        return "integer"
    if isinstance(val, float):
        return "number"
    if isinstance(val, str):
        return "string"
    if isinstance(val, list):
        return "array"
    if isinstance(val, dict):
        return "object"
    return "unknown"


def collect_types(obj, path="", types_map=None):
    types_map = types_map or defaultdict(set)
    t = infer_type(val)
    types_map[path or "."].add(t)
    if isinstance(obj, dict):
        for k, v in obj.items():
            collect_types(v, f"{path}.{k}" if path else k, types_map)
    elif isinstance(obj, list) and obj:
        collect_types(obj[0], f"{path}[]", types_map)
    return types_map


def get_ordering_signature(records):
    """Returns a string describing ordering of records (e.g. by query_index)."""
    if not records:
        return "empty"
    indices = [r.get("query_index", r.get("index", i)) for i, r in enumerate(records)]
    return "ordered" if indices == sorted(indices) else f"unordered:{indices[:5]}..."


def main():
    run_path = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("runs/latest")
    if not run_path.exists():
        print(json.dumps({"error": f"Run path not found: {run_path}"}, indent=2))
        sys.exit(1)

    result = {
        "run_path": str(run_path),
        "schema": {},
        "record_count": 0,
        "ordering_signature": "",
        "trace_inventory": [],
        "missing_trace_fields": [],
    }

    # Load outputs
    outputs_file = run_path / "outputs.json"
    if outputs_file.exists():
        with open(outputs_file) as f:
            data = json.load(f)
        records = data if isinstance(data, list) else data.get("records", [data])
    else:
        records = []
        for f in sorted(run_path.glob("*.json")):
            if f.name in ("config.json", "index.json"):
                continue
            with open(f) as fp:
                rec = json.load(fp)
                if isinstance(rec, list):
                    records.extend(rec)
                else:
                    records.append(rec)

    result["record_count"] = len(records)

    # Schema per field
    types_map = defaultdict(set)
    for r in records:
        collect_types(r, "", types_map)
    result["schema"] = {k: sorted(v) for k, v in sorted(types_map.items())}
    result["ordering_signature"] = get_ordering_signature(records)

    # Trace inventory
    traces_dir = run_path / "traces"
    if traces_dir.exists():
        result["trace_inventory"] = [p.name for p in sorted(traces_dir.glob("*.json"))]
    else:
        traces_file = run_path / "traces.json"
        if traces_file.exists():
            with open(traces_file) as f:
                traces = json.load(f)
            result["trace_inventory"] = list(traces.keys()) if isinstance(traces, dict) else [f"trace_{i}" for i in range(len(traces))]

    # Expected trace fields (from spec)
    expected_trace_fields = {"decision_point", "params", "outcome", "timestamp"}
    if result["trace_inventory"]:
        sample = traces_dir / result["trace_inventory"][0] if traces_dir.exists() else None
        if sample and sample.exists():
            with open(sample) as f:
                sample_trace = json.load(f)
            found = set(sample_trace.keys()) if isinstance(sample_trace, dict) else set()
        else:
            found = set()
        result["missing_trace_fields"] = list(expected_trace_fields - found)

    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()