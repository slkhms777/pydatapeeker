"""Helpers for pyarrow Table inspection."""

from __future__ import annotations

from typing import Any


def summarize_table(table: Any) -> dict[str, Any]:
    """Return summary metadata for a pyarrow Table."""
    row_count = int(table.num_rows)
    column_count = int(table.num_columns)
    column_summaries = []

    for field in table.schema:
        column = table.column(field.name)
        display_type = _arrow_column_display_type(column)
        column_summaries.append(
            {
                "name": str(field.name),
                "arrow_type": str(field.type),
                "display_type": display_type,
                "length": row_count,
            }
        )

    return {
        "shape": [row_count, column_count],
        "column_summaries": column_summaries,
    }


def _arrow_column_display_type(column: Any) -> str:
    """Return a compact type label for the first value in a pyarrow column."""
    if len(column) == 0:
        return str(column.type)

    try:
        scalar = column[0]
        value = scalar.as_py() if hasattr(scalar, "as_py") else scalar
    except Exception:
        return str(column.type)

    if value is None:
        return "NoneType"
    if isinstance(value, bool):
        return "bool"
    if isinstance(value, int):
        return "int"
    if isinstance(value, float):
        return "float"
    if isinstance(value, str):
        return "str"
    if isinstance(value, bytes):
        return "bytes"
    if isinstance(value, dict):
        return f"dict ({len(value)} keys)"
    if isinstance(value, list):
        return f"list (len={len(value)})"
    if isinstance(value, tuple):
        return f"tuple (len={len(value)})"
    if isinstance(value, set):
        return f"set (len={len(value)})"
    return type(value).__name__
