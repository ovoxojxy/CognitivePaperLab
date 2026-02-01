"""Basic ingestion pipeline: parse -> validate -> (optionally) save."""

from typing import Any

from parsers import parse_csv, parse_json
from storage import Storage
from validation import validate


def ingest(
    raw: str,
    format: str,
    storage: Storage | None = None,
    *,
    dry_run: bool = False,
    required: list[str] | None = None,
    types: dict[str, type] | None = None,
    min_count: int | None = None,
) -> list[dict[str, Any]]:
    """Parse, validate, optionally save. Returns records."""
    if format == "json":
        records = parse_json(raw)
    elif format == "csv":
        records = parse_csv(raw)
    else:
        raise ValueError(f"unknown format: {format}")

    validate(
        records,
        required=required or [],
        types=types or {},
        min_count=min_count,
    )

    if storage and not dry_run:
        storage.save(records)

    return records
