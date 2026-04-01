"""NumPy file loaders."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from pydatapeekr.loaders.core import register_loader


def _require_numpy() -> Any:
    try:
        import numpy as np  # type: ignore
    except ImportError as exc:
        raise ImportError("numpy file loading requires numpy to be installed") from exc
    return np


@register_loader(".npy")
def load_npy(path: Path) -> Any:
    """Load a NumPy array file."""
    np = _require_numpy()
    return np.load(path, allow_pickle=False)


@register_loader(".npz")
def load_npz(path: Path) -> dict[str, Any]:
    """Load a NumPy archive file into a plain mapping."""
    np = _require_numpy()
    with np.load(path, allow_pickle=False) as archive:
        return {key: archive[key] for key in archive.files}

