#!/usr/bin/env python3
"""Counterfactual grid runner: generate a grid of runs by flipping one knob at a time;
write runs/<ts>_grid/index.json and a short summary report.
"""

import hashlib
import json
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))
import ingestion


DEFAULT_CONFIG = {
    "format": "json",
    "order": "query_index",
    "normalize_keys": True,
    "skip_validation": False,
}

KNOBS = ["format", "order", "normalize_keys", "skip_validation"]


def _output_hash(records: list[dict]) -> str:
    return hashlib.sha256(json.dumps(records, sort_keys=True).encode()).hexdigest()[:12]


def _load_raw_input(base_run: Path) -> str:
    """Load the raw input data for re-ingestion.

    Checks for input.json first (canonical raw input), then falls back to
    outputs.json (re-process the existing pipeline output).
    """
    for candidate in ("input.json", "raw_input.json"):
        path = base_run / candidate
        if path.exists():
            return path.read_text()

    outputs_path = base_run / "outputs.json"
    if not outputs_path.exists():
        raise FileNotFoundError(
            f"No input file found in {base_run}. "
            f"Expected input.json, raw_input.json, or outputs.json"
        )
    return outputs_path.read_text()


def _run_variant(raw_input: str, variant_config: dict) -> list[dict]:
    """Re-run the ingestion pipeline with the given config."""
    return ingestion.ingest(
        raw_input,
        format=variant_config.get("format", "json"),
        skip_validation=variant_config.get("skip_validation", False),
        normalize_keys=variant_config.get("normalize_keys", False),
    )


def main():
    base_run = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("runs/20250204_surface")
    if not base_run.exists():
        print(f"Base run not found: {base_run}")
        sys.exit(1)

    with open(base_run / "config.json") as f:
        base_config = json.load(f)

    try:
        raw_input = _load_raw_input(base_run)
    except FileNotFoundError as e:
        print(f"Error: {e}")
        sys.exit(1)

    base_outputs = _run_variant(raw_input, base_config)
    base_hash = _output_hash(base_outputs)

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
    grid_index["variants"].append({
        "name": "baseline",
        "knob": None,
        "value": None,
        "output_hash": base_hash,
    })

    # Flip one knob at a time
    diff_count = 0
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

        try:
            variant_outputs = _run_variant(raw_input, variant_config)
        except Exception as e:
            variant_outputs = []
            print(f"  Warning: variant {variant_name} failed: {e}")

        with open(variant_dir / "outputs.json", "w") as f:
            json.dump(variant_outputs, f, indent=2)

        variant_hash = _output_hash(variant_outputs)
        differs = variant_hash != base_hash
        if differs:
            diff_count += 1

        grid_index["variants"].append({
            "name": variant_name,
            "knob": knob,
            "value": new_val,
            "output_hash": variant_hash,
            "differs_from_baseline": differs,
        })

    grid_index["summary"]["total"] = len(grid_index["variants"])
    grid_index["summary"]["output_diffs"] = diff_count

    with open(grid_dir / "index.json", "w") as f:
        json.dump(grid_index, f, indent=2)

    summary_report = f"""Counterfactual Grid Report: {ts}_grid
Base run: {base_run}
Variants: {grid_index['summary']['total']}
Knobs flipped: {KNOBS}
Output diffs from baseline: {diff_count}/{len(KNOBS)}
Output: {grid_dir}/index.json
"""
    with open(grid_dir / "summary.txt", "w") as f:
        f.write(summary_report)

    print(summary_report)
    print(f"Wrote {grid_dir}/index.json")


if __name__ == "__main__":
    main()
