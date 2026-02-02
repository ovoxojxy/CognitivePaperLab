#!/usr/bin/env python3
"""Run equivalent ingestion task with surface perturbations; save runs and diff outputs/traces."""

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


# Same logical data, different surface forms
PERTURBATIONS = [
    {"label": "json_baseline", "format": "json", "raw": '[{"Name": "a", "count": 1}, {"Name": "b", "count": 2}]'},
    {"label": "json_reordered", "format": "json", "raw": '[{"Name": "b", "count": 2}, {"Name": "a", "count": 1}]'},
    {"label": "csv_same_data", "format": "csv", "raw": "Name,count\na,1\nb,2"},
    {"label": "csv_reordered", "format": "csv", "raw": "Name,count\nb,2\na,1"},
    {"label": "json_alt_filename", "format": "json", "raw": '[{"Name": "a", "count": 1}, {"Name": "b", "count": 2}]'},
]


def main() -> list[dict]:
    runs = []
    for p in PERTURBATIONS:
        run_dir = get_run_dir(f"surface_{p['label']}")
        trace.init(run_dir)
        store = MemoryStorage()
        records = ingest(p["raw"], p["format"], storage=store, normalize_keys=True)
        out = {
            "label": p["label"],
            "format": p["format"],
            "record_count": len(records),
            "records": records,
            "run_dir": str(run_dir),
        }
        (run_dir / "results.json").write_text(json.dumps(out, indent=2, default=str))
        runs.append(out)
    return runs


if __name__ == "__main__":
    runs = main()
    for r in runs:
        print(r["run_dir"])
