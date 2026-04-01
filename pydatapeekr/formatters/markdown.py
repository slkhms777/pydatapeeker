"""Markdown formatter."""

from __future__ import annotations

from typing import Any


def render_markdown(inspection: dict[str, Any]) -> str:
    """Render an inspection payload as Markdown."""
    lines: list[str] = [f"- **{inspection['name']}**: {inspection.get('summary') or inspection['type']}"]
    _render_children(inspection, lines=lines, indent=1)
    return "\n".join(lines)


def _render_children(node: dict[str, Any], *, lines: list[str], indent: int) -> None:
    prefix = "  " * indent + "- "
    for key, value in node.get("meta", {}).items():
        if value in ({}, [], None, False):
            continue
        lines.append(f"{prefix}`{key}`: `{value}`")
    if node.get("sample") is not None:
        lines.append(f"{prefix}`sample`: `{node['sample']}`")
    if node.get("truncated_items"):
        lines.append(f"{prefix}`truncated_items`: `{node['truncated_items']}`")
    for child in node.get("children", []):
        lines.append(f"{prefix}**{child['name']}**: {child.get('summary') or child['type']}")
        _render_children(child, lines=lines, indent=indent + 1)

