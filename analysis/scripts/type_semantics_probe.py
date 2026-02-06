#!/usr/bin/env python3
"""Type semantics probe: flags numeric-looking strings, type distributions, coercion risk."""

import json
import re
import sys
from pathlib import Path
from collections import defaultdict


def looks_numeric(s):
    if not isinstance(s, str):
        return False
    s = s.strip()
    if not s:
        return False
    return bool(re.match(r"^-?\d+(\.\d+)?([eE][+-]?\d+)?$", s))


def collect_values(obj, path="", out=None):
    out = out or []
    if isinstance(obj, dict):
        for k, v in obj.items():
            collect_values(v, f"{path}.{k}" if path else k, out)
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            collect_values(v, f"{path}[{i}]", out)
    else:
        out.append((path, obj))
    return out


def main():
    run_path = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("runs/latest")
    if not run_path.exists():
        print(json.dumps({"error": f"Run path not found: {run_path}"}, indent=2))
        sys.exit(1)

    records = []
    for f in sorted(run_path.glob("*.json")):
        if f.name in ("config.json", "index.json"):
            continue
        try:
            with open(f) as fp:
                data = json.load(fp)
                if isinstance(data, list):
                    records.extend(data)
                else:
                    records.append(data)
        except Exception:
            pass
    outputs = run_path / "outputs.json"
    if outputs.exists():
        with open(outputs) as f:
            data = json.load(f)
        records = data if isinstance(data, list) else data.get("records", [data])

    numeric_strings = []
    type_dist = defaultdict(int)
    coercion_risk = []

    for r in records:
        for path, val in collect_values(r):
            if isinstance(val, str):
                type_dist["string"] += 1
                if looks_numeric(val):
                    numeric_strings.append({"path": path, "value": val})
                    coercion_risk.append({"path": path, "value": val, "risk": "string->number"})
            elif isinstance(val, (int, float)):
                type_dist["number"] += 1
            elif isinstance(val, bool):
                type_dist["boolean"] += 1
            elif val is None:
                type_dist["null"] += 1
            elif isinstance(val, (list, dict)):
                type_dist["complex"] += 1

    result = {
        "run_path": str(run_path),
        "numeric_looking_strings": numeric_strings[:20],
        "type_distribution": dict(type_dist),
        "coercion_risk": coercion_risk[:20],
        "total_numeric_strings": len(numeric_strings),
        "total_coercion_risks": len(coercion_risk),
    }
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()