"""High-level inspection entry points."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from datalens.formatters import format_inspection
from datalens.inspectors.core import analyze_object
from datalens.loaders import load_file


def inspect_obj(
    obj: Any,
    *,
    max_depth: int = 4,
    max_items: int = 5,
    format: str = "tree",
) -> str:
    """Inspect an in-memory object and render the result."""
    inspection = analyze_object(obj, max_depth=max_depth, max_items=max_items)
    return format_inspection(inspection, format=format)


def inspect_file(
    path: str | Path,
    *,
    max_depth: int = 4,
    max_items: int = 5,
    format: str = "tree",
) -> str:
    """Load a file, inspect it, and render the result."""
    loaded = load_file(path)
    inspection = analyze_object(
        loaded,
        name=Path(path).name,
        max_depth=max_depth,
        max_items=max_items,
    )
    return format_inspection(inspection, format=format)

