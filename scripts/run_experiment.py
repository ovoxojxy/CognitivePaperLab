#!/usr/bin/env python3
"""Run experiment script for CognitivePaperLab."""

import argparse
import json
import logging
import sys
from datetime import datetime
from pathlib import Path

RUNS_DIR = Path(__file__).resolve().parent.parent / "runs"
sys.path.insert(0, str(RUNS_DIR.parent))
import trace  # noqa: E402


def get_run_dir(exp_name: str) -> Path:
    """Create and return run directory: runs/<timestamp>_<exp_name>/"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    run_dir = RUNS_DIR / f"{timestamp}_{exp_name}"
    run_dir.mkdir(parents=True, exist_ok=True)
    return run_dir


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("exp_name", help="Experiment name for the run")
    parser.add_argument("--results", type=str, default=None, help="JSON string or path to save as results.json")
    args = parser.parse_args()

    run_dir = get_run_dir(args.exp_name)
    trace.init(run_dir)
    trace.emit("run_started", "run_experiment.main", exp_name=args.exp_name, run_dir=str(run_dir))

    # Set up log file
    log_path = run_dir / "run.log"
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s",
        handlers=[
            logging.FileHandler(log_path),
            logging.StreamHandler(),
        ],
    )
    logger = logging.getLogger(__name__)

    logger.info("Run directory: %s", run_dir)

    # Save results JSON if provided
    if args.results:
        results_path = run_dir / "results.json"
        with open(results_path, "w") as f:
            f.write(args.results if args.results.strip().startswith("{") else json.dumps({"data": args.results}))
        logger.info("Results saved to %s", results_path)
        trace.emit("results_saved", "run_experiment.main", path=str(results_path))


if __name__ == "__main__":
    main()
