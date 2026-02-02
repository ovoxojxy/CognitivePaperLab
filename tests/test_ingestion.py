"""Tests for ingestion pipeline."""

import json
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import trace
from ingestion import ingest, normalize_keys_for_ingestion, normalize_record_keys
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


def test_normalize_keys_lowercases_keys():
    """Pipeline with normalize_keys=True produces lowercased keys."""
    raw = '[{"Name": "a", "Count": 1}]'
    records = ingest(raw, "json", normalize_keys=True)
    assert list(records[0].keys()) == ["name", "count"]


def test_normalize_keys_trace_shows_wired_function():
    """Trace proves normalize_record_keys (not normalize_keys_for_ingestion) runs in pipeline."""
    run_dir = Path(tempfile.mkdtemp())
    trace.init(run_dir)
    raw = '[{"Name": "a"}]'
    ingest(raw, "json", normalize_keys=True)
    trace_path = run_dir / "trace.jsonl"
    assert trace_path.exists()
    events = [json.loads(line) for line in trace_path.read_text().strip().split("\n") if line]
    sources = [e.get("source") for e in events]
    assert "ingestion.normalize_record_keys" in sources


def test_normalize_keys_for_ingestion_is_noop():
    """normalize_keys_for_ingestion does not change keys (not wired; trap)."""
    recs = [{"Name": "x"}]
    out = normalize_keys_for_ingestion(recs)
    assert out[0].keys() == recs[0].keys()
