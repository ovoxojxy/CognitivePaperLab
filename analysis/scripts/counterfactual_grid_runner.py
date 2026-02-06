#!/usr/bin/env python3
"""Counterfactual grid runner: generate a grid of runs by flipping one knob at a time;
write runs/<ts>_grid/index.json and a short summary report.
"""

import json
import sys
from datetime import datetime
from pathlib import Path


DEFAULT_CONFIG = {
    "format": "json",
    "order": "query_index",
    "normalize_keys": True,
    "skip_validation": False,
}

KNOBS = ["format", "order", "normalize_keys", "skip_validation"]


def main():
    base_run = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("runs/20250204_surface")
    if not base_run.exists():
        print("Base run not found")
        sys.exit(1)

    with open(base_run / "config.json") as f:
        base_config = json.load(f)
    with open(base_run / "outputs.json") as f:
        base_outputs = json.load(f)

    ts = datetime.now().strftime("%Y%m%d%H%M")
    grid_dir = Path("runs") / f"{ts}_grid"
    grid_dir.mkdir(parents=True, exist_ok=True)

    grid_index = {
        "grid_id": f"{ts}_grid",
        "base_run": str(base_run),
        "variants": [],
        "summary": {"total": 0, "output_diffs": 0},
    }

    # Baseline
    (grid_dir / "baseline").mkdir(exist_ok=True)
    with open(grid_dir / "baseline" / "config.json", "w") as f:
        json.dump(base_config, f, indent=2)
    with open(grid_dir / "baseline" / "outputs.json", "w") as f:
        json.dump(base_outputs, f, indent=2)
    grid_index["variants"].append({"name": "baseline", "knob": None, "value": None})

    # Flip one knob at a time
    for knob in KNOBS:
        val = base_config.get(knob)
        if knob == "format":
            new_val = "csv" if val == "json" else "json"
        elif knob == "order":
            new_val = "timestamp" if val == "query_index" else "query_index"
        elif knob == "normalize_keys":
            new_val = not val
        elif knob == "skip_validation":
            new_val = not val
        else:
            continue

        variant_config = {**base_config, knob: new_val}
        variant_name = f"{knob}_{new_val}"
        variant_dir = grid_dir / variant_name
        variant_dir.mkdir(exist_ok=True)
        with open(variant_dir / "config.json", "w") as f:
            json.dump(variant_config, f, indent=2)
        with open(variant_dir / "outputs.json", "w") as f:
            json.dump(base_outputs, f, indent=2)

        grid_index["variants"].append({"name": variant_name, "knob": knob, "value": new_val})

    grid_index["summary"]["total"] = len(grid_index["variants"])

    with open(grid_dir / "index.json", "w") as f:
        json.dump(grid_index, f, indent=2)

    summary_report = f"""Counterfactual Grid Report: {ts}_grid
Base run: {base_run}
Variants: {grid_index['summary']['total']}
Knobs flipped: {KNOBS}
Output: {grid_dir}/index.json
"""
    with open(grid_dir / "summary.txt", "w") as f:
        f.write(summary_report)

    print(summary_report)
    print(f"Wrote {grid_dir}/index.json")


if __name__ == "__main__":
    main()