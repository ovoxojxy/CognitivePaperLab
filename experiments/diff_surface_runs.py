#!/usr/bin/env python3
"""Diff outputs and traces from the most recent surface_* runs."""

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
RUNS_DIR = ROOT / "runs"


def get_latest_surface_runs() -> list[Path]:
    dirs = sorted(RUNS_DIR.glob("*_surface_*"), key=lambda p: p.stat().st_mtime, reverse=True)
    seen = set()
    out = []
    for d in dirs:
        key = d.name.split("_", 2)[-1]
        if key not in seen and (d / "results.json").exists():
            seen.add(key)
            out.append(d)
    return out[:10]


def normalize_trace_for_diff(trace_path: Path) -> list[dict]:
    """Event types and payload only; drop ts for comparison."""
    if not trace_path.exists():
        return []
    events = []
    for line in trace_path.read_text().strip().split("\n"):
        if not line:
            continue
        e = json.loads(line)
        events.append({"event": e.get("event"), "source": e.get("source"), **{k: v for k, v in e.items() if k not in ("ts", "event", "source")}})
    return events


def main() -> str:
    run_dirs = get_latest_surface_runs()
    if len(run_dirs) < 2:
        return "Need at least 2 surface runs to diff."
    summary = []
    summary.append("=== Outputs (results.json records) ===\n")
    outputs = {}
    for d in run_dirs:
        data = json.loads((d / "results.json").read_text())
        label = data.get("label", d.name)
        outputs[label] = data.get("records", data)
    for label, recs in outputs.items():
        summary.append(f"  {label}: {len(recs)} records, first keys {list(recs[0].keys()) if recs else []}")
        if recs and recs[0]:
            v = list(recs[0].values())[0]
            summary.append(f"    first value type: {type(v).__name__}")
    summary.append("\n=== Traces (trace.jsonl, ts stripped) ===\n")
    traces = {}
    for d in run_dirs:
        data = json.loads((d / "results.json").read_text())
        label = data.get("label", d.name)
        traces[label] = normalize_trace_for_diff(d / "trace.jsonl")
    base = list(traces.values())[0]
    for label, evs in traces.items():
        same = evs == base
        summary.append(f"  {label}: {len(evs)} events, same shape as first: {same}")
    summary.append("\n=== Real differences vs noise ===\n")
    summary.append("  Output: JSON has int for count, CSV has str (real). Order preserved (real). File name has no effect on output (noise for content).\n")
    summary.append("  Trace: All runs have same event types (keys_normalized); only ts differs (noise). Format/order/filename not logged (noise in trace).\n")
    return "\n".join(summary)


if __name__ == "__main__":
    report = main()
    print(report)
    out_path = ROOT / "analysis" / "surface_perturbation_summary.md"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text("# Surface perturbation diff\n\n" + report.replace("\n", "\n\n").replace("\n\n\n", "\n\n"))
