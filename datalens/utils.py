"""Shared helper functions for DataLens."""

from __future__ import annotations

from collections import Counter
from typing import Any, Iterable


def safe_repr(value: Any, max_length: int = 80) -> str:
    """Return a shortened repr for display."""
    try:
        text = repr(value)
    except Exception:
        text = f"<unrepresentable {type(value).__name__}>"
    if len(text) <= max_length:
        return text
    return text[: max_length - 3] + "..."


def type_name(value: Any) -> str:
    """Return a stable display name for a value's type."""
    value_type = type(value)
    if value_type.__module__ == "builtins":
        return value_type.__name__
    return f"{value_type.__module__}.{value_type.__name__}"


def distribution(values: Iterable[Any]) -> dict[str, int]:
    """Count value types in an iterable."""
    counter = Counter(type_name(value) for value in values)
    return dict(sorted(counter.items(), key=lambda item: (-item[1], item[0])))


def truncate_mapping_items(items: list[tuple[Any, Any]], max_items: int) -> tuple[list[tuple[Any, Any]], int]:
    """Return the displayed mapping items and the hidden count."""
    shown = items[:max_items]
    hidden = max(len(items) - len(shown), 0)
    return shown, hidden


def truncate_sequence_items(items: list[Any], max_items: int) -> tuple[list[Any], int]:
    """Return the displayed sequence items and the hidden count."""
    shown = items[:max_items]
    hidden = max(len(items) - len(shown), 0)
    return shown, hidden

