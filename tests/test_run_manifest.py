"""Regression test: write_manifest must use trace_schema_version (not trace_schemaversion)."""

import tempfile
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from analysis.run_manifest import write_manifest, read_manifest


def test_manifest_has_trace_schema_version():
    """Manifest must have trace_schema_version key."""
    with tempfile.TemporaryDirectory() as td:
        run_path = Path(td)
        write_manifest(run_path, {"format": "json"}, "test")
        m = read_manifest(run_path)
        assert m is not None
        assert "trace_schema_version" in m, "manifest must have trace_schema_version (not typo trace_schemaversion)"
        assert m["trace_schema_version"] == "v1"
