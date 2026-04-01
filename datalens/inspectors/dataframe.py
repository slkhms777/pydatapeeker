"""Helpers for pandas DataFrame inspection."""

from __future__ import annotations

from typing import Any

from datalens.utils import safe_repr


def summarize_dataframe(df: Any, *, max_items: int) -> dict[str, Any]:
    """Return summary metadata for a pandas DataFrame."""
    columns = [str(column) for column in df.columns]
    dtypes = {str(column): str(dtype) for column, dtype in df.dtypes.items()}
    sample_rows = df.head(max_items).to_dict(orient="records")
    null_count = {str(column): int(value) for column, value in df.isnull().sum().items()}

    mixed_type_columns: dict[str, dict[str, int]] = {}
    column_type_counts: dict[str, dict[str, int]] = {}
    for column in df.columns:
        counts: dict[str, int] = {}
        for value in df[column].head(max_items * 10).tolist():
            key = type(value).__name__
            counts[key] = counts.get(key, 0) + 1
        column_type_counts[str(column)] = counts
        if len(counts) > 1:
            mixed_type_columns[str(column)] = counts

    concise_samples = [{str(key): _summarize_cell(value) for key, value in row.items()} for row in sample_rows]
    column_examples = {
        str(column): _summarize_cell(df[column].iloc[0]) for column in df.columns if len(df[column]) > 0
    }
    column_summaries = [
        {
            "name": str(column),
            "dtype": dtypes[str(column)],
            "null_count": null_count[str(column)],
            "example": column_examples.get(str(column), "n/a"),
            "python_types": column_type_counts[str(column)],
            "mixed_types": str(column) in mixed_type_columns,
        }
        for column in df.columns
    ]

    return {
        "shape": [int(df.shape[0]), int(df.shape[1])],
        "column_count": len(columns),
        "dtypes": dtypes,
        "null_count": null_count,
        "column_examples": column_examples,
        "column_summaries": column_summaries,
        "sample_rows": concise_samples,
        "mixed_type_columns": mixed_type_columns,
    }


def _summarize_cell(value: Any) -> str:
    """Return a concise structural preview for a DataFrame cell."""
    if value is None:
        return "None"
    if isinstance(value, (bool, int, float, str)):
        return safe_repr(value, max_length=40)
    if _looks_like_numpy_scalar(value):
        return safe_repr(_numpy_scalar_to_python(value), max_length=40)
    if _looks_like_ndarray(value):
        return f"ndarray(shape={_safe_shape(value)}, dtype={getattr(value, 'dtype', 'unknown')})"
    if _looks_like_torch_tensor(value):
        return f"torch tensor(shape={_safe_shape(value)}, dtype={getattr(value, 'dtype', 'unknown')})"
    if isinstance(value, dict):
        keys = list(value.keys())
        preview = ", ".join(str(key) for key in keys[:3])
        suffix = ", ..." if len(keys) > 3 else ""
        return f"dict(keys=[{preview}{suffix}])"
    if isinstance(value, (list, tuple, set)):
        return f"{type(value).__name__}(len={len(value)})"
    return safe_repr(value, max_length=60)


def _looks_like_ndarray(value: Any) -> bool:
    return hasattr(value, "shape") and hasattr(value, "dtype") and value.__class__.__module__.startswith("numpy")


def _looks_like_numpy_scalar(value: Any) -> bool:
    module_name = value.__class__.__module__
    shape = getattr(value, "shape", None)
    return module_name.startswith("numpy") and shape == ()


def _looks_like_torch_tensor(value: Any) -> bool:
    module_name = value.__class__.__module__
    return hasattr(value, "shape") and hasattr(value, "dtype") and module_name.startswith("torch")


def _safe_shape(value: Any) -> Any:
    try:
        return tuple(value.shape)
    except Exception:
        return "unknown"


def _numpy_scalar_to_python(value: Any) -> Any:
    try:
        return value.item()
    except Exception:
        return value
