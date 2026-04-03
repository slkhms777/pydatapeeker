"""High-level inspection entry points."""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

from pydatapeekr.formatters import format_inspection
from pydatapeekr.inspectors.core import analyze_object
from pydatapeekr.loaders import load_file


def inspect_obj(
    obj: Any,
    *,
    max_depth: int = 4,
    max_dict_items: int = 8,
    max_list_items: int = 1,
    show_sample: bool = False,
    format: str = "tree",
    write_to_file: str | Path | bool | None = None,
) -> str:
    """Inspect an in-memory object and render the result."""
    inspection = analyze_object(
        obj,
        max_depth=max_depth,
        max_dict_items=max_dict_items,
        max_list_items=max_list_items,
        show_sample=show_sample,
    )
    output = format_inspection(inspection, format=format)
    if write_to_file is not None:
        target = resolve_output_path(
            inspection_name="root",
            requested_path=write_to_file,
        )
        target.write_text(output, encoding="utf-8")
    return output


def display_obj(
    obj: Any,
    *,
    max_depth: int = 4,
    max_dict_items: int = 8,
    max_list_items: int = 1,
    show_sample: bool = False,
    format: str = "tree",
    style: str = "-",
    stream: Any | None = None,
) -> str:
    """Inspect an in-memory object and print it with a terminal-friendly wrapper."""
    output = inspect_obj(
        obj,
        max_depth=max_depth,
        max_dict_items=max_dict_items,
        max_list_items=max_list_items,
        show_sample=show_sample,
        format=format,
        write_to_file=None,
    )
    wrapped = wrap_output(output, style=style)
    (stream or sys.stdout).write(wrapped)
    return wrapped


def inspect_file(
    path: str | Path,
    *,
    max_depth: int = 4,
    max_dict_items: int = 8,
    max_list_items: int = 1,
    show_sample: bool = False,
    format: str = "tree",
    write_to_file: str | Path | bool | None = None,
) -> str:
    """Load a file, inspect it, and render the result."""
    input_path = Path(path)
    loaded = load_file(input_path)
    inspection = analyze_object(
        loaded,
        name=input_path.name,
        max_depth=max_depth,
        max_dict_items=max_dict_items,
        max_list_items=max_list_items,
        show_sample=show_sample,
    )
    output = format_inspection(inspection, format=format)
    if write_to_file is not None:
        target = resolve_output_path(
            inspection_name=input_path.name,
            requested_path=write_to_file,
            base_dir=input_path.parent,
        )
        target.write_text(output, encoding="utf-8")
    return output


def display_file(
    path: str | Path,
    *,
    max_depth: int = 4,
    max_dict_items: int = 8,
    max_list_items: int = 1,
    show_sample: bool = False,
    format: str = "tree",
    style: str = "-",
    stream: Any | None = None,
) -> str:
    """Inspect a file and print it with a terminal-friendly wrapper."""
    output = inspect_file(
        path,
        max_depth=max_depth,
        max_dict_items=max_dict_items,
        max_list_items=max_list_items,
        show_sample=show_sample,
        format=format,
        write_to_file=None,
    )
    wrapped = wrap_output(output, style=style)
    (stream or sys.stdout).write(wrapped)
    return wrapped


def wrap_output(text: str, *, style: str = "-") -> str:
    """Wrap inspection text for clearer terminal display."""
    if style == "plain":
        return text
    if style in {"-", "#", "`"}:
        content_width = _wrapper_content_width(text)
        side_width = (content_width - 12) // 2
        banner = style * side_width + " PEEKR INFO " + style * side_width
        footer = style * len(banner)
        return f"\n{banner}\n{text}\n{footer}\n"
    raise ValueError(f"Unsupported display style: {style}")


def _wrapper_content_width(text: str) -> int:
    """Return the target banner width for wrapped display text."""
    lines = text.splitlines() or [text]
    max_width = max(len(line) for line in lines) if lines else 0
    content_width = max(20, max_width)
    if content_width % 2 == 1:
        content_width += 1
    return content_width


def resolve_output_path(
    *,
    inspection_name: str,
    requested_path: str | Path | bool,
    base_dir: str | Path | None = None,
) -> Path:
    """Resolve a writable output path for persisted inspection results."""
    if requested_path is True:
        target = Path(base_dir or ".") / f"data_info_{inspection_name}.txt"
    else:
        target = Path(requested_path)
    if target.suffix.lower() not in {".txt", ".md", ".markdown"}:
        raise ValueError("Output file must use one of: .txt, .md, .markdown")
    return target
