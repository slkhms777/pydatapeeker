"""YAML loader."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from datalens.loaders.core import register_loader


@register_loader(".yaml", ".yml")
def load_yaml(path: Path) -> Any:
    """Load a YAML file, with a JSON-subset fallback when PyYAML is unavailable."""
    text = path.read_text(encoding="utf-8")
    try:
        import yaml  # type: ignore
    except ImportError:
        try:
            return json.loads(text)
        except json.JSONDecodeError as exc:
            raise ImportError(
                "yaml loading requires PyYAML to be installed unless the file is valid JSON-compatible YAML"
            ) from exc
    return yaml.safe_load(text)

