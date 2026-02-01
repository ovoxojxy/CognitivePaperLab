"""Tests for validation."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pytest

from validation import SchemaError, SemanticError, validate


def test_valid_record():
    validate([{"name": "x", "count": 3}], required=["name", "count"], min_count=0)


def test_missing_required_field():
    with pytest.raises(SchemaError) as exc:
        validate([{"name": "x"}], required=["name", "count"])
    assert "missing required field: count" in str(exc.value)
    assert exc.value.index == 0


def test_wrong_type():
    with pytest.raises(SchemaError) as exc:
        validate([{"name": "x", "count": "not-a-number"}], types={"count": int})
    assert "must be int" in str(exc.value)


def test_semantic_count_negative():
    with pytest.raises(SemanticError) as exc:
        validate([{"name": "x", "count": -1}], min_count=0)
    assert "count must be >= 0" in str(exc.value)
    assert exc.value.index == 0


def test_semantic_valid_zero():
    validate([{"name": "x", "count": 0}], min_count=0)


def test_empty_required_field():
    with pytest.raises(SchemaError) as exc:
        validate([{"name": "", "count": 1}], required=["name", "count"])
    assert "required field name is empty" in str(exc.value)
