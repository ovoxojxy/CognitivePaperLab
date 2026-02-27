"""Basic ingestion pipeline: parse -> validate -> (optionally) save."""

from typing import Any

from parsers import parse_csv, parse_json
from storage import Storage
from validation import validate

try:
    import trace as _trace
except ImportError:
    _trace = None


def normalize_record_keys(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Lowercase all keys in each record. Used when normalize_keys=True."""
    out = [{k.lower(): v for k, v in r.items()} for r in records]
    if _trace:
        _trace.emit("keys_normalized", "ingestion.normalize_record_keys", record_count=len(out))
    return out


def ingest(
    raw: str,
    format: str,
    storage: Storage | None = None,
    *,
    dry_run: bool = False,
    skip_validation: bool = False,
    normalize_keys: bool = False,
    required: list[str] | None = None,
    types: dict[str, type] | None = None,
    min_count: int | None = None,
) -> list[dict[str, Any]]:
    """Parse, validate (unless skipped), optionally save. Returns records."""
    if format == "json":
        records = parse_json(raw)
    elif format == "csv":
        records = parse_csv(raw)
    else:
        raise ValueError(f"unknown format: {format}")

    # NOTE: Key normalization uses normalize_record_keys (lowercase only).
    # We intentionally do NOT apply canonical snake_case normalization here
    # because it would change output hashes and invalidate the counterfactual
    # grid baselines. See discussion on the normalize_keys_for_ingestion removal.
    if normalize_keys:
        records = normalize_record_keys(records)

    if not skip_validation:
        validate(
            records,
            required=required or [],
            types=types or {},
            min_count=min_count,
        )

    if storage and not dry_run:
        storage.save(records)

    return records
