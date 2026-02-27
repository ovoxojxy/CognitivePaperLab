#!/usr/bin/env python3
"""Explainability diff: compares two runs, outputs raw and normalized diffs,
trace diffs, and a 'trace explains output?' judgment. Writes explainability_report.json."""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))
from analysis.normalize_output import normalize_output
from analysis.run_manifest import read_manifest


TRACE_NAMING_V1 = "v1"  # trace_0.json, trace_3.json
TRACE_NAMING_V2 = "v2"  # trace_0_decision.json, trace_0_commit_author.json


def infer_trace_naming(traces_dir: Path) -> str:
    """Infer trace naming version from filenames."""
    if not traces_dir.exists():
        return "none"
    files = list(traces_dir.glob("*.json"))
    if not files:
        return "none"
    names = [f.stem for f in files]
    # v2: trace_0_validate_config, trace_0_commit_author
    if any("_" in n and n.count("_") >= 2 for n in names):
        return TRACE_NAMING_V2
    return TRACE_NAMING_V1


def load_records(path):
    p = Path(path)
    records = []
    if (p / "outputs.json").exists():
        with open(p / "outputs.json") as f:
            data = json.load(f)
        records = data if isinstance(data, list) else data.get("records", [data])
    else:
        for f in sorted(p.glob("*.json")):
            if f.name in ("config.json", "index.json", "manifest.json"):
                continue
            with open(f) as fp:
                rec = json.load(fp)
                records.append(rec)
    return {r.get("query_index", r.get("index", i)): r for i, r in enumerate(records)}


def load_traces(path):
    """Load traces. Handles both v1 (trace_0) and v2 (trace_0_decision) naming."""
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
        print("Usage: explainability_diff.py <run_a> <run_b> [--out report_dir] [--max-diffs N]")
        sys.exit(1)
    run_a, run_b = Path(sys.argv[1]), Path(sys.argv[2])
    out_dir = None
    max_diffs = None
    args = sys.argv[3:]
    for i, a in enumerate(args):
        if a == "--out" and i + 1 < len(args):
            out_dir = Path(args[i + 1])
        elif a == "--max-diffs" and i + 1 < len(args):
            max_diffs = int(args[i + 1])

    if not run_a.exists() or not run_b.exists():
        print(json.dumps({"error": "One or both run paths not found"}))
        sys.exit(1)

    recs_a = load_records(run_a)
    recs_b = load_records(run_b)
    traces_a = load_traces(run_a)
    traces_b = load_traces(run_b)

    # Trace naming version check
    naming_a = infer_trace_naming(run_a / "traces")
    naming_b = infer_trace_naming(run_b / "traces")
    trace_naming_warning = None
    if naming_a != naming_b and naming_a != "none" and naming_b != "none":
        trace_naming_warning = f"Trace naming mismatch: {naming_a} vs {naming_b}. Proceeding best-effort."
        print(f"WARNING: {trace_naming_warning}", file=sys.stderr)

    # Raw output diffs
    output_diffs_raw = []
    for idx in set(recs_a.keys()) | set(recs_b.keys()):
        ra, rb = recs_a.get(idx), recs_b.get(idx)
        if ra != rb:
            output_diffs_raw.extend(deep_diff(ra or {}, rb or {}, f"query_{idx}"))

    # Normalized output diffs
    norm_a = {k: normalize_output(v) for k, v in recs_a.items()}
    norm_b = {k: normalize_output(v) for k, v in recs_b.items()}
    output_diffs_normalized = []
    for idx in set(norm_a.keys()) | set(norm_b.keys()):
        ra, rb = norm_a.get(idx), norm_b.get(idx)
        if ra != rb:
            output_diffs_normalized.extend(deep_diff(ra or {}, rb or {}, f"query_{idx}"))

    # Trace diffs
    trace_diffs = []
    for k in set(traces_a.keys()) | set(traces_b.keys()):
        ta, tb = traces_a.get(k), traces_b.get(k)
        if ta != tb:
            trace_diffs.extend(deep_diff(ta or {}, tb or {}, f"trace_{k}"))

    # Judgment
    output_diffs = output_diffs_raw  # use raw for judgment
    judgment = "uncertain"
    reasons = []
    if output_diffs and not trace_diffs:
        judgment = "traces_do_not_explain"
        reasons.append("Outputs differ but traces are identical or missing; no trace-level explanation for output diff")
    elif output_diffs and trace_diffs:
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

    # Normalization note
    norm_note = ""
    if output_diffs_raw != output_diffs_normalized:
        raw_paths = {d.get("path") for d in output_diffs_raw}
        norm_paths = {d.get("path") for d in output_diffs_normalized}
        removed = raw_paths - norm_paths
        added = norm_paths - raw_paths
        norm_note = f"Normalization changed diffs. Removed from raw: {removed or 'none'}. Added in normalized: {added or 'none'}. Normalization coerces record_count, count, total, num_records, and item_count (string->int via INT_COERCION_FIELDS) and may mask or expose type-only diffs."
    else:
        norm_note = "Raw and normalized diffs are identical."

    raw_out = output_diffs_raw[:max_diffs] if max_diffs is not None else output_diffs_raw
    norm_out = output_diffs_normalized[:max_diffs] if max_diffs is not None else output_diffs_normalized
    trace_out = trace_diffs[:max_diffs] if max_diffs is not None else trace_diffs

    result = {
        "run_a": str(run_a),
        "run_b": str(run_b),
        "trace_naming_warning": trace_naming_warning,
        "raw_output_diffs": raw_out,
        "normalized_output_diffs": norm_out,
        "trace_diffs": trace_out,
        "judgment": judgment,
        "reasons": reasons,
        "normalization_note": norm_note,
    }

    if max_diffs is not None:
        for key, full in [
            ("raw_output_diffs", output_diffs_raw),
            ("normalized_output_diffs", output_diffs_normalized),
            ("trace_diffs", trace_diffs),
        ]:
            if len(full) > max_diffs:
                result[f"{key}_total"] = len(full)
                result[f"{key}_truncated"] = True

    print(json.dumps(result, indent=2))

    if out_dir:
        out_dir = Path(out_dir)
        out_dir.mkdir(parents=True, exist_ok=True)
        report_path = out_dir / "explainability_report.json"
        with open(report_path, "w") as f:
            json.dump(result, f, indent=2)
        print(f"Wrote {report_path}", file=sys.stderr)


if __name__ == "__main__":
    main()
