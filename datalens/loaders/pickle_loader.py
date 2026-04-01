"""Pickle file loader."""

from __future__ import annotations

import pickle
import warnings
from pathlib import Path
from typing import Any

from datalens.loaders.core import register_loader
from datalens.loaders.pickle_static import StaticPickleData


@register_loader(".pkl", ".pickle")
def load_pickle(path: Path) -> Any:
    """Load a pickle file with a safety warning."""
    warnings.warn(
        f"Loading pickle file {path} can execute arbitrary code. Only open trusted files.",
        RuntimeWarning,
        stacklevel=2,
    )
    with path.open("rb") as handle:
        try:
            return pickle.load(handle)
        except ModuleNotFoundError:
            handle.seek(0)
            return StaticPickleData(data=handle.read(), root_name=path.name)
