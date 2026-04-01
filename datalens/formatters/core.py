"""Select and run inspection formatters."""

from __future__ import annotations

from datalens.formatters.markdown import render_markdown
from datalens.formatters.tree import render_tree


def format_inspection(inspection: dict, *, format: str) -> str:
    """Format an inspection payload into the requested output format."""
    normalized = format.lower()
    if normalized == "tree":
        return render_tree(inspection)
    if normalized in {"markdown", "md"}:
        return render_markdown(inspection)
    raise ValueError(f"Unsupported format: {format}")
