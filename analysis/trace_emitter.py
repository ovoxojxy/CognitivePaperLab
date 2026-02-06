"""Trace emitter: emits trace events when processing run outputs.
Used by run pipeline to record decision points.
"""

import json
from pathlib import Path


def emit_trace(run_path: Path, query_index: int, decision_point: str, params: dict, outcome: str) -> None:
    """Emit a trace event for a decision point."""
    traces_dir = run_path / "traces"
    traces_dir.mkdir(parents=True, exist_ok=True)
    # Emit trace for all decision points including commit_author_selection
    trace = {"decision_point": decision_point, "params": params, "outcome": outcome}
    out = traces_dir / f"trace_{query_index}_{decision_point}.json"
    with open(out, "w") as f:
        json.dump(trace, f, indent=2)
