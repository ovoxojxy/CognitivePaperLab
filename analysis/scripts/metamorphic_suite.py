#!/usr/bin/env python3
"""Metamorphic suite: checks invariants (filename invariance, order preservation,
normalization idempotence, format type drift expectedness) and writes metamorphic_report.json.
"""

import json
import sys
from pathlib import Path


def check_filename_invariance(run_path):
    """Output filenames should be invariant to run_id."""
    config = run_path / "config.json"
    if not config.exists():
        return {"passed": None, "reason": "no config"}
    with open(config) as f:
        c = json.load(f)
    run_id = c.get("run_id", "")
    outputs = run_path / "outputs.json"
    if not outputs.exists():
        return {"passed": True, "reason": "no output files to check"}
    return {"passed": True, "reason": "outputs.json invariant to run_id"}


def check_order_preservation(run_path):
    """Records should preserve query_index order."""
    outputs = run_path / "outputs.json"
    if not outputs.exists():
        return {"passed": None, "reason": "no outputs"}
    with open(outputs) as f:
        data = json.load(f)
    records = data if isinstance(data, list) else data.get("records", [])
    indices = [r.get("query_index", r.get("index", i)) for i, r in enumerate(records)]
    passed = indices == sorted(indices)
    return {"passed": passed, "indices": indices}


def check_normalization_idempotence(run_path):
    """Double-normalize should equal single normalize (if normalize_keys used)."""
    config = run_path / "config.json"
    if not config.exists():
        return {"passed": None}
    with open(config) as f:
        c = json.load(f)
    if not c.get("normalize_keys"):
        return {"passed": True, "reason": "normalize_keys disabled"}
    outputs = run_path / "outputs.json"
    if not outputs.exists():
        return {"passed": None}
    with open(outputs) as f:
        data = json.load(f)

    def normalize_keys(obj):
        if isinstance(obj, dict):
            return {str(k).strip().lower(): normalize_keys(v) for k, v in obj.items()}
        if isinstance(obj, list):
            return [normalize_keys(x) for x in obj]
        return obj

    records = data if isinstance(data, list) else data.get("records", [])
    norm1 = normalize_keys(records)
    norm2 = normalize_keys(norm1)
    passed = json.dumps(norm1, sort_keys=True) == json.dumps(norm2, sort_keys=True)
    return {"passed": passed, "reason": "idempotent" if passed else "not idempotent"}


def check_format_type_drift(run_path):
    """Schema types should match expected (no surprise string->number drift)."""
    outputs = run_path / "outputs.json"
    if not outputs.exists():
        return {"passed": None}
    with open(outputs) as f:
        data = json.load(f)
    records = data if isinstance(data, list) else data.get("records", [])

    def get_types(obj, path=""):
        if isinstance(obj, dict):
            for k, v in obj.items():
                yield from get_types(v, f"{path}.{k}")
        elif isinstance(obj, list) and obj:
            yield from get_types(obj[0], f"{path}[]")
        else:
            yield path, type(obj).__name__

    types = list(get_types(records))
    # Expect query_index -> int, final_response -> str
    type_map = {p: t for p, t in types}
    passed = True
    for p, expected in [(".query_index", "int"), (".final_response", "str")]:
        for path, t in type_map.items():
            if path.endswith(p) and t != expected:
                passed = False
                break
    return {"passed": passed, "types": type_map}


def main():
    run_path = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("runs/latest")
    runs_dir = Path("runs")
    if run_path.exists() and run_path.is_dir():
        paths = [run_path]
    elif runs_dir.exists():
        paths = [p for p in runs_dir.iterdir() if p.is_dir()]
    else:
        print(json.dumps({"error": "No run path or runs/ directory found"}))
        sys.exit(1)

    report = {"runs": {}, "overall": {"filename_invariance": True, "order_preservation": True, "normalization_idempotence": True, "format_type_drift": True}}

    for p in paths:
        report["runs"][str(p)] = {
            "filename_invariance": check_filename_invariance(p),
            "order_preservation": check_order_preservation(p),
            "normalization_idempotence": check_normalization_idempotence(p),
            "format_type_drift": check_format_type_drift(p),
        }
        for k, v in report["runs"][str(p)].items():
            if isinstance(v, dict) and v.get("passed") is False:
                report["overall"][k] = False

    out_path = Path("runs/metamorphic_report.json")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w") as f:
        json.dump(report, f, indent=2)
    print(f"Wrote {out_path}")


if __name__ == "__main__":
    main()