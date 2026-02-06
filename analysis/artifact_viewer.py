#!/usr/bin/env python3
"""Given a run folder, print inferable vs not inferable based on trace coverage + manifest."""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from analysis.run_manifest import read_manifest

# From trace_coverage_matrix: what is in traces vs results vs neither
TRACE_COVERED = {"validate_config params", "validate_config outcome", "config status", "re-query decision"}
RESULT_COVERED = {"format", "order", "normalize_keys", "skip_validation", "validate_config outcome"}
NEITHER = {"rate_limit value (Turn 1)"}


def main():
    run_path = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("runs/20250204_surface")
    if not run_path.exists():
        print(f"Run path not found: {run_path}")
        sys.exit(1)

    manifest = read_manifest(run_path)
    traces_dir = run_path / "traces"
    outputs = run_path / "outputs.json"

    inferable = []
    not_inferable = []

    # From manifest
    if manifest:
        inferable.append("config (format, order, normalize_keys, skip_validation)")
        inferable.append("input_provenance")
        inferable.append("trace_schema_version")
        inferable.append("normalize_output_version")
    else:
        not_inferable.append("manifest metadata (no manifest)")

    # From traces
    if traces_dir.exists():
        trace_files = list(traces_dir.glob("*.json"))
        if trace_files:
            inferable.append(f"trace events ({len(trace_files)} files)")
            # Check for decision_point, params, outcome
            sample = json.loads((traces_dir / trace_files[0].name).read_text())
            if "decision_point" in sample:
                inferable.append("decision_point per trace")
            if "params" in sample:
                inferable.append("params per trace")
            if "outcome" in sample:
                inferable.append("outcome per trace")
            # Trace coverage gaps
            not_inferable.append("rate_limit from Turn 1 (conversation only)")
            not_inferable.append("commit_author decision (unless traced)")
        else:
            not_inferable.append("trace events (empty traces dir)")
    else:
        not_inferable.append("trace events (no traces dir)")

    # From outputs
    if outputs.exists():
        inferable.append("final_response per query")
        inferable.append("query_index ordering")
    else:
        not_inferable.append("output records (no outputs.json)")

    print("=== INFERABLE from artifacts ===")
    for x in sorted(set(inferable)):
        print(f"  + {x}")
    print("\n=== NOT INFERABLE from artifacts ===")
    for x in sorted(set(not_inferable)):
        print(f"  - {x}")
