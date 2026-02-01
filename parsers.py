"""Parse JSON and CSV into a common record format: list of dicts."""

import csv
import io
import json
from typing import Any


def parse_json(raw: str) -> list[dict[str, Any]]:
    """Parse JSON into list of records. Single object becomes one-item list."""
    data = json.loads(raw)
    if isinstance(data, dict):
        return [data]
    return list(data)


def parse_csv(raw: str) -> list[dict[str, Any]]:
    """Parse CSV into list of records. First row = headers. Keys lowercased."""
    reader = csv.DictReader(io.StringIO(raw))
    return [{k.lower(): v for k, v in row.items()} for row in reader]
