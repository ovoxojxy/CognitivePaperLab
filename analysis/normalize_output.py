"""Normalize run outputs for comparison.
"""

import json
from typing import Any


def normalize_value(val: Any, path: str = "", key: str = "") -> Any:
    """Normalize a value."""
    if isinstance(val, dict):
        return {k: normalize_value(v, f"{path}.{k}" if path else k, k) for k, v in val.items()}
    if isinstance(val, list):
        return [normalize_value(v, f"{path}[{i}]", "") for i, v in enumerate(val)]
    if isinstance(val, str) and val.isdigit():
        # Coerce numeric strings to int for record_count and count for consistent comparison
        if key in ("record_count", "count"):
            return int(val)
    return val


def normalize_output(obj: Any, path: str = "") -> Any:
    """Normalize an output record for comparison."""
    return normalize_value(obj, path, "")
