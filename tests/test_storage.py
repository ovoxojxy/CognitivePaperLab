"""Tests for storage backends."""

import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from storage import MemoryStorage, SQLiteStorage, get_storage


def test_memory_save_load():
    store = MemoryStorage()
    records = [{"a": 1}, {"b": 2}]
    store.save(records)
    assert store.load() == records


def test_memory_load_empty():
    store = MemoryStorage()
    assert store.load() == []


def test_sqlite_save_load():
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        path = f.name
    try:
        store = SQLiteStorage(path)
        records = [{"name": "x", "count": 3}]
        store.save(records)
        assert store.load() == records
    finally:
        Path(path).unlink(missing_ok=True)


def test_sqlite_persists():
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        path = f.name
    try:
        store = SQLiteStorage(path)
        store.save([{"x": 1}])
        store2 = SQLiteStorage(path)
        assert store2.load() == [{"x": 1}]
    finally:
        Path(path).unlink(missing_ok=True)


def test_get_storage_memory():
    store = get_storage("memory")
    assert isinstance(store, MemoryStorage)


def test_get_storage_sqlite():
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        path = f.name
    try:
        store = get_storage("sqlite", path=path)
        assert isinstance(store, SQLiteStorage)
        store.save([{"a": 1}])
        assert store.load() == [{"a": 1}]
    finally:
        Path(path).unlink(missing_ok=True)
