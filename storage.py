"""Storage backends with a common interface."""

import json
import sqlite3
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any


class Storage(ABC):
    """Common interface: save and load records."""

    @abstractmethod
    def save(self, records: list[dict[str, Any]]) -> None:
        """Persist records."""
        ...

    @abstractmethod
    def load(self) -> list[dict[str, Any]]:
        """Load records. Returns [] if empty."""
        ...


class MemoryStorage(Storage):
    """In-memory storage."""

    def __init__(self) -> None:
        self._records: list[dict[str, Any]] = []

    def save(self, records: list[dict[str, Any]]) -> None:
        self._records = list(records)

    def load(self) -> list[dict[str, Any]]:
        return list(self._records)


class SQLiteStorage(Storage):
    """SQLite-backed persistent storage."""

    def __init__(self, path: str | Path) -> None:
        self._path = Path(path)
        self._path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _init_db(self) -> None:
        with sqlite3.connect(self._path) as conn:
            conn.execute(
                "CREATE TABLE IF NOT EXISTS records (data TEXT)"
            )

    def save(self, records: list[dict[str, Any]]) -> None:
        with sqlite3.connect(self._path) as conn:
            conn.execute("DELETE FROM records")
            conn.execute(
                "INSERT INTO records (data) VALUES (?)",
                (json.dumps(records),)
            )

    def load(self) -> list[dict[str, Any]]:
        with sqlite3.connect(self._path) as conn:
            row = conn.execute("SELECT data FROM records LIMIT 1").fetchone()
        if row is None:
            return []
        return json.loads(row[0])


def get_storage(backend: str, path: str | Path | None = None) -> Storage:
    """Get storage by config. backend='memory' or 'sqlite'."""
    if backend == "memory":
        return MemoryStorage()
    if backend == "sqlite":
        if path is None:
            raise ValueError("sqlite backend requires path")
        return SQLiteStorage(path)
    raise ValueError(f"unknown backend: {backend}")
