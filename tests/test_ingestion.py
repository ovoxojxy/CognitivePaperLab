"""Tests for ingestion pipeline."""

import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from ingestion import ingest
from storage import MemoryStorage, SQLiteStorage


def test_ingest_json_to_memory():
    store = MemoryStorage()
    raw = '[{"name": "x", "count": 3}]'
    records = ingest(raw, "json", storage=store)
    assert records == [{"name": "x", "count": 3}]
    assert store.load() == records


def test_ingest_csv_to_memory():
    store = MemoryStorage()
    raw = "name,count\nx,3\ny,5"
    records = ingest(raw, "csv", storage=store)
    assert len(records) == 2
    assert store.load() == records


def test_dry_run_does_not_write():
    store = MemoryStorage()
    raw = '[{"name": "x", "count": 3}]'
    records = ingest(raw, "json", storage=store, dry_run=True)
    assert records == [{"name": "x", "count": 3}]
    assert store.load() == []


def test_dry_run_sqlite_no_file():
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        path = f.name
    Path(path).unlink(missing_ok=True)
    store = SQLiteStorage(path)
    raw = '[{"name": "x", "count": 3}]'
    records = ingest(raw, "json", storage=store, dry_run=True)
    assert records == [{"name": "x", "count": 3}]
    assert store.load() == []
