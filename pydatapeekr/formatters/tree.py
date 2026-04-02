"""Tree formatter for CLI-friendly output."""

from __future__ import annotations

import json
from collections.abc import Mapping, Sequence
from typing import Any

from pydatapeekr.utils import safe_repr


def render_tree(inspection: dict[str, Any]) -> str:
    """Render an inspection tree as plain text."""
    lines: list[str] = []
    _render_node(inspection, lines=lines, ancestor_prefix="", is_last=True, is_root=True)
    return "\n".join(lines)


def _render_node(
    node: dict[str, Any],
    *,
    lines: list[str],
    ancestor_prefix: str,
    is_last: bool,
    is_root: bool = False,
) -> None:
    connector = "" if is_root else ("└── " if is_last else "├── ")
    label_name = _format_label(node["name"], quoted=node.get("quote_name", False))
    label = f"{label_name}: {node.get('summary') or node['type']}"
    lines.append(ancestor_prefix + connector + label)

    meta_entries = _meta_entries(node.get("meta", {}))
    if node.get("sample") is not None:
        meta_entries.append(("line", f"<sample>: {node['sample']}"))
    children = node.get("children", [])
    trailing_line = None
    if node.get("truncated_items"):
        trailing_line = f"... {node['truncated_items']} more item(s)"
    child_prefix = ancestor_prefix + ("" if is_root else ("    " if is_last else "│   "))

    total_items = len(meta_entries) + len(children) + (1 if trailing_line else 0)
    rendered_items = 0

    for entry_kind, entry_value in meta_entries:
        rendered_items += 1
        entry_is_last = rendered_items == total_items
        if entry_kind == "line":
            connector = "└── " if entry_is_last else "├── "
            lines.append(child_prefix + connector + entry_value)
            continue
        label_text, value = entry_value
        _render_value(
            label_text,
            value,
            lines=lines,
            ancestor_prefix=child_prefix,
            is_last=entry_is_last,
        )

    for child in children:
        rendered_items += 1
        _render_node(
            child,
            lines=lines,
            ancestor_prefix=child_prefix,
            is_last=rendered_items == total_items,
        )

    if trailing_line is not None:
        rendered_items += 1
        connector = "└── " if rendered_items == total_items else "├── "
        lines.append(child_prefix + connector + trailing_line)


def _meta_entries(meta: dict[str, Any]) -> list[tuple[str, Any]]:
    entries: list[tuple[str, Any]] = []
    for key, value in meta.items():
        if value in ({}, [], None, False):
            continue
        label = _format_meta_label(key)
        if _is_stat_meta_key(key) and isinstance(value, Mapping):
            entries.append(("line", f"{label}: {_format_inline_mapping(value)}"))
            continue
        if _is_tree_container(value):
            entries.append(("tree", (label, value)))
        else:
            entries.append(("line", f"{label}: {_format_scalar(value)}"))
    return entries


def _render_value(
    label: str,
    value: Any,
    *,
    lines: list[str],
    ancestor_prefix: str,
    is_last: bool,
) -> None:
    connector = "└── " if is_last else "├── "
    if isinstance(value, Mapping):
        lines.append(ancestor_prefix + connector + f"{label}: dict ({len(value)} keys)")
        child_prefix = ancestor_prefix + ("    " if is_last else "│   ")
        items = list(value.items())
        for index, (child_key, child_value) in enumerate(items):
            _render_value(
                _format_label(str(child_key), quoted=True),
                child_value,
                lines=lines,
                ancestor_prefix=child_prefix,
                is_last=index == len(items) - 1,
            )
        return

    if _is_sequence_value(value):
        sequence = list(value)
        sequence_type = type(value).__name__
        lines.append(ancestor_prefix + connector + f"{label}: {sequence_type} (len={len(sequence)})")
        if not sequence:
            return
        child_prefix = ancestor_prefix + ("    " if is_last else "│   ")
        has_more = len(sequence) > 1
        _render_value(
            "[0]",
            sequence[0],
            lines=lines,
            ancestor_prefix=child_prefix,
            is_last=not has_more,
        )
        if has_more:
            lines.append(child_prefix + "└── " + f"... {len(sequence) - 1} more item(s)")
        return

    lines.append(ancestor_prefix + connector + f"{label}: {_format_scalar(value)}")


def _format_scalar(value: Any) -> str:
    if isinstance(value, str):
        return value
    return safe_repr(value, max_length=80)


def _format_label(label: str, *, quoted: bool) -> str:
    if not quoted:
        return label
    escaped = label.replace("\\", "\\\\").replace('"', '\\"')
    return f'"{escaped}"'


def _format_inline_mapping(value: Mapping[Any, Any]) -> str:
    normalized = {str(key): item for key, item in value.items()}
    return json.dumps(normalized, ensure_ascii=True)


def _is_stat_meta_key(key: str) -> bool:
    return key in {"attribute_count", "key_types", "type_distribution"} or key.endswith("_count")


def _format_meta_label(key: str) -> str:
    if _is_stat_meta_key(key):
        return f"<{key}>"
    return key


def _is_tree_container(value: Any) -> bool:
    return isinstance(value, Mapping) or _is_sequence_value(value)


def _is_sequence_value(value: Any) -> bool:
    return isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray))
