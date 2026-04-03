"""Pickle file loader."""

from __future__ import annotations

import pickle
import warnings
from pathlib import Path
from typing import Any

from pydatapeekr.loaders.core import register_loader
from pydatapeekr.loaders.pickle_static import StaticPickleData


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
            return _load_pickle_with_compatibility(handle)
        except (ImportError, UnicodeDecodeError, AttributeError, ValueError):
            handle.seek(0)
            return StaticPickleData(data=handle.read(), root_name=path.name)


def _load_pickle_with_compatibility(handle: Any) -> Any:
    """Load pickles with fallbacks for Python 2/legacy NumPy payloads."""
    try:
        return _safe_pickle_load(handle)
    except UnicodeDecodeError:
        # Many older Python 2 pickles store 8-bit strings that Python 3 otherwise
        # tries to decode as ASCII during unpickling. latin1 is the standard
        # compatibility fallback for these legacy scientific-model assets.
        handle.seek(0)
        return _safe_pickle_load(handle, encoding="latin1")


def _safe_pickle_load(handle: Any, *, encoding: str | None = None) -> Any:
    """Load a pickle while suppressing noisy legacy NumPy deprecation warnings."""
    with warnings.catch_warnings():
        # Some old model pickles reconstruct NumPy dtypes in ways that now emit a
        # VisibleDeprecationWarning on NumPy 2.4+, even when loading still works.
        # Suppress that noise so the user sees either the parsed result or the
        # actionable fallback error instead of a scary warning wall.
        message = r"dtype\(\): align should be passed as Python or NumPy boolean"
        warnings.filterwarnings("ignore", message=message)
        if encoding is None:
            return pickle.load(handle)
        return pickle.load(handle, encoding=encoding)
