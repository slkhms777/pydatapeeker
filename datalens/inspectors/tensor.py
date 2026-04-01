"""Helpers for torch tensor inspection."""

from __future__ import annotations

from typing import Any


def summarize_tensor(tensor: Any, *, max_items: int) -> dict[str, Any]:
    """Return summary metadata for a torch Tensor."""
    if getattr(tensor, "numel", lambda: 0)() == 0:
        preview: list[Any] = []
    else:
        preview = tensor.detach().cpu().flatten()[:max_items].tolist()
    return {
        "shape": list(tensor.shape),
        "dtype": str(tensor.dtype),
        "sample": preview,
    }


def tensor_display_type(tensor: Any) -> str:
    """Return a compact one-line display label for a torch Tensor."""
    return f"torch.Tensor(shape={tuple(tensor.shape)}, dtype={tensor.dtype})"
