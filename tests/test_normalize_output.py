"""Regression tests for normalize_output: consistent coercion of count field."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from analysis.normalize_output import normalize_output


def test_normalize_count_field():
    """count and record_count should both be coerced to int."""
    obj = {"count": "5", "record_count": "1"}
    result = normalize_output(obj)
    assert result["record_count"] == 1
    assert result["count"] == 5