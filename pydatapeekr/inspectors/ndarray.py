"""Helpers for numpy array inspection."""

from __future__ import annotations

from typing import Any


def summarize_ndarray(array: Any, *, max_items: int) -> dict[str, Any]:
    """Return summary metadata for a numpy ndarray."""
    return {
        "shape": list(array.shape),
        "dtype": str(array.dtype),
    }
