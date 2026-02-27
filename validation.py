"""Schema and semantic validation for records."""

from typing import Any


class ValidationError(Exception):
    """Base for validation errors."""

    def __init__(self, msg: str, index: int | None = None):
        super().__init__(msg)
        self.msg = msg
        self.index = index


class SchemaError(ValidationError):
    """Missing required field or wrong type."""


class SemanticError(ValidationError):
    """Technically valid but logically wrong."""


def validate(
    records: list[dict[str, Any]],
    *,
    required: list[str] | None = None,
    types: dict[str, type] | None = None,
    min_count: int | None = None,
) -> None:
    """Validate records. Raises SchemaError or SemanticError on failure."""
    required = required or []
    types = types or {}

    for i, rec in enumerate(records):
        for field in required:
            if field not in rec:
                raise SchemaError(f"missing required field: {field}", index=i)
            if rec[field] is None or rec[field] == "":
                raise SchemaError(f"required field {field} is empty", index=i)

        for field, expected in types.items():
            if field not in rec:
                continue
            val = rec[field]
            if expected == int:
                try:
                    int(val)
                except (TypeError, ValueError):
                    raise SchemaError(f"{field} must be int, got {type(val).__name__}", index=i)
            elif not isinstance(val, expected):
                raise SchemaError(f"{field} must be {expected.__name__}, got {type(val).__name__}", index=i)

        if min_count is not None and "count" in rec:
            try:
                c = int(rec["count"])
            except (TypeError, ValueError):
                raise SchemaError(f"count field is not numeric: {rec['count']!r}", index=i)
            else:
                if c < min_count:
                    raise SemanticError(f"count must be >= {min_count}, got {c}", index=i)
