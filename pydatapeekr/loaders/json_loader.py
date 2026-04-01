"""JSON and JSONL loaders."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from pydatapeekr.loaders.core import register_loader


@register_loader(".json")
def load_json(path: Path) -> Any:
    """Load a standard JSON file."""
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


@register_loader(".jsonl")
def load_jsonl(path: Path) -> list[Any]:
    """Load a JSON Lines file."""
    rows: list[Any] = []
    with path.open("r", encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            stripped = line.strip()
            if not stripped:
                continue
            try:
                rows.append(json.loads(stripped))
            except json.JSONDecodeError as exc:
                raise ValueError(f"Invalid JSONL at line {line_number}") from exc
    return rows

