#!/usr/bin/env python3
"""Explainability diff: compares two runs, outputs observed output diffs, trace diffs,
and a 'trace explains output?' judgment with reasons.
"""

import json
import sys
from pathlib import Path


def load_records(path):
    p = Path(path)
    records = []
    if (p / "outputs.json").exists():
        with open(p / "outputs.json") as f:
            data = json.load(f)
        records = data if isinstance(data, list) else data.get("records", [data])
    else:
        for f in sorted(p.glob("*.json")):
            if f.name in ("config.json", "index.json"):
                continue
            with open(f) as fp:
                rec = json.load(fp)
                records.append(rec)
    return {r.get("query_index", r.get("index", i)): r for i, r in enumerate(records)}


def load_traces(path):
    p = Path(path)
    traces = {}
    if (p / "traces.json").exists():
        with open(p / "traces.json") as f:
            traces = json.load(f)
    elif (p / "traces").exists():
        for f in (p / "traces").glob("*.json"):
            with open(f) as fp:
                traces[f.stem] = json.load(fp)
    return traces


def deep_diff(a, b, path=""):
    diffs = []
    if type(a) != type(b):
        diffs.append({"path": path, "a_type": type(a).__name__, "b_type": type(b).__name__, "a": str(a)[:100], "b": str(b)[:100]})
        return diffs
    if isinstance(a, dict):
        all_keys = set(a.keys()) | set(b.keys())
        for k in all_keys:
            va, vb = a.get(k), b.get(k)
            if va != vb:
                if isinstance(va, (dict, list)) and isinstance(vb, (dict, list)):
                    diffs.extend(deep_diff(va, vb, f"{path}.{k}" if path else k))
                else:
                    diffs.append({"path": f"{path}.{k}" if path else k, "a": va, "b": vb})
    elif isinstance(a, list):
        if len(a) != len(b):
            diffs.append({"path": path, "len_a": len(a), "len_b": len(b)})
        for i, (va, vb) in enumerate(zip(a, b)):
            if va != vb:
                diffs.extend(deep_diff(va, vb, f"{path}[{i}]"))
    elif a != b:
        diffs.append({"path": path, "a": a, "b": b})
    return diffs


def main():
    if len(sys.argv) < 3:
        print("Usage: explainability_diff.py <run_a> <run_b>")
        sys.exit(1)
    run_a, run_b = Path(sys.argv[1]), Path(sys.argv[2])
    if not run_a.exists() or not run_b.exists():
        print(json.dumps({"error": "One or both run paths not found"}))
        sys.exit(1)

    recs_a = load_records(run_a)
    recs_b = load_records(run_b)
    traces_a = load_traces(run_a)
    traces_b = load_traces(run_b)

    output_diffs = []
    trace_diffs = []
    for idx in set(recs_a.keys()) | set(recs_b.keys()):
        ra, rb = recs_a.get(idx), recs_b.get(idx)
        if ra != rb:
            output_diffs.extend(deep_diff(ra or {}, rb or {}, f"query_{idx}"))
    for k in set(traces_a.keys()) | set(traces_b.keys()):
        ta, tb = traces_a.get(k), traces_b.get(k)
        if ta != tb:
            trace_diffs.extend(deep_diff(ta or {}, tb or {}, f"trace_{k}"))

    # Judgment: does trace explain output?
    judgment = "uncertain"
    reasons = []
    if output_diffs and not trace_diffs:
        judgment = "traces_do_not_explain"
        reasons.append("Outputs differ but traces are identical or missing; no trace-level explanation for output diff")
    elif output_diffs and trace_diffs:
        # Check if trace diffs correlate with output diffs
        trace_paths = {d.get("path", "") for d in trace_diffs}
        output_paths = {d.get("path", "") for d in output_diffs}
        if trace_paths & output_paths or any("decision" in str(t) for t in trace_diffs):
            judgment = "traces_may_explain"
            reasons.append("Trace diffs overlap with or precede output diffs")
        else:
            judgment = "traces_do_not_explain"
            reasons.append("Trace diffs exist but do not obviously explain output diffs (no decision_point overlap)")
    elif not output_diffs:
        judgment = "no_output_diff"
        reasons.append("Outputs are identical; no explanation needed")

    result = {
        "run_a": str(run_a),
        "run_b": str(run_b),
        "observed_output_diffs": output_diffs[:30],
        "trace_diffs": trace_diffs[:30],
        "judgment": judgment,
        "reasons": reasons,
    }
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()