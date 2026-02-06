"""Regression tests for trace_emitter: emit trace for commit_author_selection."""

import tempfile
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from analysis.trace_emitter import emit_trace


def test_emit_trace_commit_author_selection():
    """commit_author_selection should emit a trace."""
    with tempfile.TemporaryDirectory() as td:
        run_path = Path(td)
        emit_trace(run_path, 0, "commit_author_selection", {"author": "Brent"}, "success")
        traces_dir = run_path / "traces"
        assert traces_dir.exists()
        trace_files = list(traces_dir.glob("*.json"))
        assert len(trace_files) >= 1
        content = trace_files[0].read_text()
        assert "commit_author_selection" in content
        assert "Brent" in content