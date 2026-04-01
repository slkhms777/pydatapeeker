"""Loader registry implementation."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Callable

Loader = Callable[[Path], Any]

_REGISTRY: dict[str, Loader] = {}


class PyDataPeekrLoadError(RuntimeError):
    """Raised when a file cannot be loaded."""


def register_loader(*suffixes: str) -> Callable[[Loader], Loader]:
    """Register a loader for one or more filename suffixes."""

    def decorator(func: Loader) -> Loader:
        for suffix in suffixes:
            _REGISTRY[suffix.lower()] = func
        return func

    return decorator


def load_file(path: str | Path) -> Any:
    """Load a file based on its suffix."""
    file_path = Path(path)
    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")
    suffix = file_path.suffix.lower()
    loader = _REGISTRY.get(suffix)
    if loader is None:
        raise PyDataPeekrLoadError(
            f"Unsupported file type: {suffix or '<no extension>'}. "
            f"Supported types: {', '.join(sorted(_REGISTRY))}"
        )
    try:
        return loader(file_path)
    except Exception as exc:
        raise PyDataPeekrLoadError(f"Failed to load {file_path}: {exc}") from exc

