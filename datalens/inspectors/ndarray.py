"""Helpers for numpy array inspection."""

from __future__ import annotations

from typing import Any


def summarize_ndarray(array: Any, *, max_items: int) -> dict[str, Any]:
    """Return summary metadata for a numpy ndarray."""
    preview = array.flatten()[:max_items].tolist() if getattr(array, "size", 0) else []
    return {
        "shape": list(array.shape),
        "dtype": str(array.dtype),
        "sample": preview,
    }

