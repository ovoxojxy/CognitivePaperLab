#!/usr/bin/env python3
"""Run same input under different ingestion configs and save each run to runs/."""

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


SAMPLE_INPUT = '[{"Name": "a", "count": 1}, {"Name": "b", "count": 2}]'

CONFIGS = [
    {"name": "default", "skip_validation": False, "normalize_keys": False},
    {"name": "normalize_keys", "skip_validation": False, "normalize_keys": True},
    {"name": "skip_validation", "skip_validation": True, "normalize_keys": False},
]


def main() -> None:
    runs_created = []
    for cfg in CONFIGS:
        run_dir = get_run_dir(f"ingestion_{cfg['name']}")
        trace.init(run_dir)
        trace.emit("config_started", "run_ingestion_configs.main", config=cfg["name"])

        store = MemoryStorage()
        records = ingest(
            SAMPLE_INPUT,
            "json",
            storage=store,
            dry_run=False,
            skip_validation=cfg["skip_validation"],
            normalize_keys=cfg["normalize_keys"],
        )

        result = {
            "config": cfg,
            "record_count": len(records),
            "first_record_keys": list(records[0].keys()) if records else [],
        }
        results_path = run_dir / "results.json"
        with open(results_path, "w") as f:
            json.dump(result, f, indent=2)
        trace.emit("ingestion_done", "run_ingestion_configs.main", run_dir=str(run_dir), record_count=len(records))
        runs_created.append({"config": cfg["name"], "run_dir": str(run_dir), "record_count": len(records)})
    return runs_created


if __name__ == "__main__":
    runs = main()
    for r in runs:
        print(f"  {r['config']}: {r['run_dir']} ({r['record_count']} records)")
