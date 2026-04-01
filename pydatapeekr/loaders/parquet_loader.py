"""Parquet loader."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from pydatapeekr.loaders.core import register_loader


@register_loader(".parquet")
def load_parquet(path: Path) -> Any:
    """Load a parquet file using pandas when available."""
    try:
        import pandas as pd  # type: ignore
    except ImportError:
        pd = None

    if pd is not None:
        return pd.read_parquet(path)

    try:
        import pyarrow.parquet as pq  # type: ignore
    except ImportError as exc:
        raise ImportError("parquet loading requires pandas or pyarrow to be installed") from exc
    return pq.read_table(path)

