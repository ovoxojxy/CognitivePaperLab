"""Regression tests for normalize_output: consistent coercion of count fields."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from analysis.normalize_output import normalize_output, INT_COERCION_FIELDS


def test_normalize_count_field():
    """count and record_count should both be coerced to int."""
    obj = {"count": "5", "record_count": "1"}
    result = normalize_output(obj)
    assert result["record_count"] == 1
    assert result["count"] == 5


def test_normalize_total_field():
    """total should be coerced to int when it's a numeric string."""
    obj = {"total": "42", "name": "test"}
    result = normalize_output(obj)
    assert result["total"] == 42
    assert result["name"] == "test"


def test_normalize_num_records_field():
    """num_records should be coerced to int."""
    obj = {"num_records": "10"}
    result = normalize_output(obj)
    assert result["num_records"] == 10


def test_normalize_item_count_field():
    """item_count should be coerced to int."""
    obj = {"item_count": "3"}
    result = normalize_output(obj)
    assert result["item_count"] == 3


def test_all_coercion_fields_in_one_record():
    """All allowlisted fields should coerce in a single record."""
    obj = {k: "7" for k in INT_COERCION_FIELDS}
    result = normalize_output(obj)
    for k in INT_COERCION_FIELDS:
        assert result[k] == 7, f"{k} was not coerced to int"


def test_non_allowlisted_field_not_coerced():
    """Fields not in the allowlist should stay as strings."""
    obj = {"query_index": "5", "total": "5"}
    result = normalize_output(obj)
    assert result["query_index"] == "5"
    assert result["total"] == 5


def test_nested_coercion():
    """Coercion should work inside nested dicts."""
    obj = {"summary": {"total": "100", "label": "test"}}
    result = normalize_output(obj)
    assert result["summary"]["total"] == 100
    assert result["summary"]["label"] == "test"


def test_non_numeric_string_not_coerced():
    """Non-numeric strings should never be coerced even for allowlisted keys."""
    obj = {"total": "N/A", "count": "unknown"}
    result = normalize_output(obj)
    assert result["total"] == "N/A"
    assert result["count"] == "unknown"
