#!/usr/bin/env python3
"""Run same logical input as JSON and as CSV; compare traces to show format is not logged."""

import json
import sys
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
RUNS_DIR = ROOT / "runs"
sys.path.insert(0, str(ROOT))

import trace
from ingestion import ingest
from storage import MemoryStorage


def get_run_dir(exp_name: str) -> Path:
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    run_dir = RUNS_DIR / f"{timestamp}_{exp_name}"
    run_dir.mkdir(parents=True, exist_ok=True)
    return run_dir


# Same logical records: one as JSON, one as CSV
JSON_INPUT = '[{"Name": "a", "count": 1}, {"Name": "b", "count": 2}]'
CSV_INPUT = "Name,count\na,1\nb,2"


def main() -> None:
    results = []
    for fmt, raw, label in [("json", JSON_INPUT, "as_json"), ("csv", CSV_INPUT, "as_csv")]:
        run_dir = get_run_dir(f"format_observability_{label}")
        trace.init(run_dir)
        store = MemoryStorage()
        records = ingest(raw, fmt, storage=store, normalize_keys=True)
        result = {"format": fmt, "run_dir": str(run_dir), "record_count": len(records)}
        (run_dir / "meta.json").write_text(json.dumps({"format": fmt}, indent=2))
        results.append(result)
    return results


if __name__ == "__main__":
    runs = main()
    for r in runs:
        print(f"  {r['format']}: {r['run_dir']}")
