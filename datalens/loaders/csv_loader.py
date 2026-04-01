"""CSV and TSV loaders."""

from __future__ import annotations

import csv
from pathlib import Path
from typing import Any

from datalens.loaders.core import register_loader


def _load_delimited(path: Path, delimiter: str) -> Any:
    try:
        import pandas as pd  # type: ignore
    except ImportError:
        with path.open("r", encoding="utf-8", newline="") as handle:
            return list(csv.DictReader(handle, delimiter=delimiter))
    return pd.read_csv(path, sep=delimiter)


@register_loader(".csv")
def load_csv(path: Path) -> Any:
    """Load a CSV file."""
    return _load_delimited(path, delimiter=",")


@register_loader(".tsv")
def load_tsv(path: Path) -> Any:
    """Load a TSV file."""
    return _load_delimited(path, delimiter="\t")

