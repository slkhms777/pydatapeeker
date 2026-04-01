"""JSON formatter."""

from __future__ import annotations

import json
from typing import Any


def render_json(inspection: dict[str, Any]) -> str:
    """Render an inspection payload as JSON."""
    return json.dumps(inspection, indent=2, ensure_ascii=False)

