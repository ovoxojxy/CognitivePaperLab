"""Minimal trace/event logger for run-time evidence."""

import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

_output = None


def init(run_dir: Path) -> None:
    """Start writing trace events to run_dir/trace.jsonl."""
    global _output
    _output = open(run_dir / "trace.jsonl", "w")


def emit(event: str, source: str, **data: Any) -> None:
    """Emit a structured event. source = where it came from (e.g. module.fn)."""
    record = {"ts": datetime.now().isoformat(), "event": event, "source": source, **data}
    line = json.dumps(record) + "\n"
    if _output:
        _output.write(line)
        _output.flush()
    else:
        sys.stderr.write(line)
