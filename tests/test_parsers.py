"""Tests for JSON and CSV parsers."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from parsers import parse_csv, parse_json


def test_parse_json_array():
    raw = '[{"a": 1}, {"a": 2}]'
    got = parse_json(raw)
    assert got == [{"a": 1}, {"a": 2}]


def test_parse_json_single_object():
    raw = '{"Name": "x", "count": 3}'
    got = parse_json(raw)
    assert got == [{"Name": "x", "count": 3}]


def test_parse_csv():
    raw = "Name,count\nx,3\ny,5"
    got = parse_csv(raw)
    assert got == [{"name": "x", "count": "3"}, {"name": "y", "count": "5"}]


def test_parse_csv_lowercases_keys():
    """CSV lowercases header names; JSON keeps original casing."""
    json_raw = '{"Name": "a"}'
    csv_raw = "Name\na"
    assert parse_json(json_raw)[0]["Name"] == "a"
    assert "Name" not in parse_csv(csv_raw)[0]
    assert parse_csv(csv_raw)[0]["name"] == "a"
