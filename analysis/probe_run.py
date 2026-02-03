#!/usr/bin/env python3
"""Introspect a run folder: schema, types per field, record count, ordering signature, trace inventory."""

import argparse
import json
from collections import Counter
from pathlib import Path


def load_run(run_dir: Path) -> tuple[list[dict] | None, list[dict], dict | None]:
    run_dir = Path(run_dir)
    records = None
    results_path = run_dir / "results.json"
    if results_path.exists():
        data = json.loads(results_path.read_text())
        records = data.get("records") if isinstance(data, dict) else None
    trace_events = []
    trace_path = run_dir / "trace.jsonl"
    if trace_path.exists():
        for line in trace_path.read_text().strip().split("\n"):
            if line:
                trace_events.append(json.loads(line))
    meta = None
    meta_path = run_dir / "meta.json"
    if meta_path.exists():
        meta = json.loads(meta_path.read_text())
    return records, trace_events, meta


def schema_and_types(records: list[dict]) -> dict[str, set[str]]:
    field_types: dict[str, set[str]] = {}
    for rec in records:
        for k, v in rec.items():
            field_types.setdefault(k, set()).add(type(v).__name__)
    return field_types


def ordering_signature(records: list[dict], key: str | None = None) -> str:
    if not records:
        return "(empty)"
    key = key or (list(records[0].keys())[0] if records[0] else None)
    if not key:
        return "(no keys)"
    vals = [rec.get(key) for rec in records]
    return ",".join(str(v) for v in vals)


def trace_inventory(events: list[dict]) -> list[tuple[str, str, int]]:
    c = Counter((e.get("event"), e.get("source")) for e in events)
    return [(event, source, count) for (event, source), count in c.most_common()]


def main() -> None:
    parser = argparse.ArgumentParser(description="Summarize a run folder")
    parser.add_argument("run_dir", type=Path, help="Path to run directory (e.g. runs/20260201_192324_surface_json_baseline)")
    args = parser.parse_args()
    records, trace_events, meta = load_run(args.run_dir)

    print(f"run: {args.run_dir.name}\n")
    if meta:
        print(f"meta: {json.dumps(meta)}\n")

    if records is not None:
        print(f"record_count: {len(records)}")
        schema = schema_and_types(records)
        print("schema + types:")
        for field in sorted(schema.keys()):
            print(f"  {field}: {', '.join(sorted(schema[field]))}")
        print(f"ordering_signature (first field): {ordering_signature(records)}")
    else:
        print("(no results.json with 'records' in this run)")

    print("\ntrace.jsonl inventory:")
    for event, source, count in trace_inventory(trace_events):
        print(f"  {event} | {source} x{count}")
    if not trace_events:
        print("  (no trace events)")


if __name__ == "__main__":
    main()
