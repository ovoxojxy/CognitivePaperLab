#!/usr/bin/env python3
"""Probe type semantics from run output: numeric-but-strings, type distributions."""

import argparse
import json
from collections import Counter, defaultdict
from pathlib import Path


def load_records(run_dir: Path) -> list[dict] | None:
    run_dir = Path(run_dir)
    results_path = run_dir / "results.json"
    if not results_path.exists():
        return None
    data = json.loads(results_path.read_text())
    return data.get("records") if isinstance(data, dict) else None


def looks_numeric(s: str) -> bool:
    if not isinstance(s, str) or not s.strip():
        return False
    try:
        float(s.strip())
        return True
    except ValueError:
        return False


def probe(records: list[dict]) -> dict:
    field_types: dict[str, Counter[str]] = defaultdict(Counter)
    field_numeric_string_count: dict[str, int] = defaultdict(int)
    field_total: dict[str, int] = defaultdict(int)
    for rec in records:
        for k, v in rec.items():
            field_types[k].update([type(v).__name__])
            field_total[k] += 1
            if isinstance(v, str) and looks_numeric(v):
                field_numeric_string_count[k] += 1
    return {
        "field_types": dict(field_types),
        "field_total": dict(field_total),
        "numeric_string_count": dict(field_numeric_string_count),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Type semantics probe on run output")
    parser.add_argument("run_dir", type=Path, help="Path to run directory")
    args = parser.parse_args()
    records = load_records(args.run_dir)
    if not records:
        print("No records in this run (missing results.json or 'records' key).")
        return

    out = probe(records)
    print(f"run: {args.run_dir.name}\n")
    print("type distribution per field:")
    for field in sorted(out["field_types"].keys()):
        dist = out["field_types"][field]
        total = out["field_total"][field]
        line = f"  {field}: " + ", ".join(f"{t}={c}" for t, c in dist.most_common())
        print(line)
        nnum = out["numeric_string_count"].get(field, 0)
        if nnum > 0:
            print(f"    -> {nnum}/{total} values are string-but-numeric (possible CSV/JSON type gap)")


if __name__ == "__main__":
    main()
