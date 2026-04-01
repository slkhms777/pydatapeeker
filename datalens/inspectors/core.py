"""Recursive object analysis."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any

from datalens.inspectors.dataframe import summarize_dataframe
from datalens.inspectors.ndarray import summarize_ndarray
from datalens.loaders.pickle_static import PrebuiltInspection
from datalens.utils import distribution, safe_repr, truncate_mapping_items, truncate_sequence_items, type_name


def analyze_object(
    obj: Any,
    *,
    name: str = "root",
    max_depth: int = 4,
    max_items: int = 5,
) -> dict[str, Any]:
    """Analyze any supported Python object into a serializable tree."""
    if isinstance(obj, PrebuiltInspection):
        payload = copy_payload(obj.payload)
        payload["name"] = name
        return payload
    active_path: set[int] = set()
    return _analyze(
        obj,
        name=name,
        depth=0,
        max_depth=max_depth,
        max_items=max_items,
        active_path=active_path,
    )


def _analyze(
    obj: Any,
    *,
    name: str,
    depth: int,
    max_depth: int,
    max_items: int,
    active_path: set[int],
) -> dict[str, Any]:
    node: dict[str, Any] = {
        "name": str(name),
        "type": type_name(obj),
        "depth": depth,
        "summary": "",
    }

    tracked = False
    object_id = id(obj)
    if _should_track_identity(obj):
        if object_id in active_path:
            node["summary"] = f"{type_name(obj)} (circular reference)"
            node["circular"] = True
            return node
        active_path.add(object_id)
        tracked = True

    try:
        if depth >= max_depth:
            node["summary"] = f"{type_name(obj)} (max depth reached)"
            node["sample"] = safe_repr(obj)
            return node

        dataframe_type = _import_type("pandas", "DataFrame")
        table_type = _import_type("pyarrow", "Table")
        ndarray_type = _import_type("numpy", "ndarray")

        if dataframe_type is not None and isinstance(obj, dataframe_type):
            summary = summarize_dataframe(obj, max_items=max_items)
            node["summary"] = f"DataFrame {tuple(summary['shape'])}"
            node["meta"] = {
                "shape": summary["shape"],
                "column_count": summary["column_count"],
                "sample_rows": summary["sample_rows"],
            }
            node["children"] = [
                {
                    "name": column["name"],
                    "type": "dataframe_column",
                    "depth": depth + 1,
                    "summary": f"column ({column['dtype']})",
                    "meta": _dataframe_column_meta(column),
                }
                for column in summary.get("column_summaries", [])[:max_items]
            ]
            hidden_columns = max(len(summary.get("column_summaries", [])) - len(node["children"]), 0)
            if hidden_columns:
                node["truncated_items"] = hidden_columns
            return node

        if table_type is not None and isinstance(obj, table_type):
            schema_text = [f"{field.name}: {field.type}" for field in obj.schema]
            node["summary"] = f"pyarrow.Table ({obj.num_rows} rows, {obj.num_columns} columns)"
            node["meta"] = {
                "shape": [obj.num_rows, obj.num_columns],
                "schema": schema_text[:max_items],
                "truncated_schema_fields": max(len(schema_text) - max_items, 0),
            }
            return node

        if ndarray_type is not None and isinstance(obj, ndarray_type):
            summary = summarize_ndarray(obj, max_items=max_items)
            node["summary"] = f"ndarray {tuple(summary['shape'])}"
            node["meta"] = summary
            return node

        if isinstance(obj, Mapping):
            return _analyze_mapping(
                obj,
                node=node,
                depth=depth,
                max_depth=max_depth,
                max_items=max_items,
                active_path=active_path,
            )

        if isinstance(obj, (list, tuple, set)):
            return _analyze_sequence(
                obj,
                node=node,
                depth=depth,
                max_depth=max_depth,
                max_items=max_items,
                active_path=active_path,
            )

        if _is_basic_type(obj):
            node["summary"] = type_name(obj)
            node["sample"] = safe_repr(obj)
            return node

        if hasattr(obj, "__dict__"):
            attrs = vars(obj)
            node["summary"] = f"{type_name(obj)} object"
            node["meta"] = {"attribute_count": len(attrs)}
            node["children"] = [
                _analyze(
                    value,
                    name=str(key),
                    depth=depth + 1,
                    max_depth=max_depth,
                    max_items=max_items,
                    active_path=active_path,
                )
                for key, value in list(attrs.items())[:max_items]
            ]
            hidden = max(len(attrs) - len(node["children"]), 0)
            if hidden:
                node["truncated_items"] = hidden
            return node

        node["summary"] = type_name(obj)
        node["sample"] = safe_repr(obj)
        return node
    finally:
        if tracked:
            active_path.remove(object_id)


def _analyze_mapping(
    obj: Mapping[Any, Any],
    *,
    node: dict[str, Any],
    depth: int,
    max_depth: int,
    max_items: int,
    active_path: set[int],
) -> dict[str, Any]:
    items = list(obj.items())
    shown, hidden = truncate_mapping_items(items, max_items)
    node["summary"] = f"dict ({len(obj)} keys)"
    node["meta"] = {"length": len(obj), "key_types": distribution(obj.keys())}
    node["children"] = [
        _analyze(
            value,
            name=str(key),
            depth=depth + 1,
            max_depth=max_depth,
            max_items=max_items,
            active_path=active_path,
        )
        for key, value in shown
    ]
    if hidden:
        node["truncated_items"] = hidden
    return node


def _analyze_sequence(
    obj: Sequence[Any] | set[Any],
    *,
    node: dict[str, Any],
    depth: int,
    max_depth: int,
    max_items: int,
    active_path: set[int],
) -> dict[str, Any]:
    sequence = list(obj)
    shown, hidden = truncate_sequence_items(sequence, max_items)
    type_counts = distribution(sequence)
    node["summary"] = f"{type(obj).__name__} (len={len(sequence)})"
    node["meta"] = {
        "length": len(sequence),
        "type_distribution": type_counts,
        "mixed_types": len(type_counts) > 1,
    }
    node["children"] = [
        _analyze(
            value,
            name=f"[{index}]",
            depth=depth + 1,
            max_depth=max_depth,
            max_items=max_items,
            active_path=active_path,
        )
        for index, value in enumerate(shown)
    ]
    if hidden:
        node["truncated_items"] = hidden
    return node


def _is_basic_type(obj: Any) -> bool:
    return isinstance(obj, (str, int, float, bool, type(None), bytes))


def _should_track_identity(obj: Any) -> bool:
    return isinstance(obj, (Mapping, list, tuple, set)) or hasattr(obj, "__dict__")


def _import_type(module_name: str, type_name_str: str) -> Any | None:
    try:
        module = __import__(module_name, fromlist=[type_name_str])
    except ImportError:
        return None
    return getattr(module, type_name_str, None)


def copy_payload(payload: dict[str, Any]) -> dict[str, Any]:
    """Create a defensive copy of a prebuilt inspection tree."""
    copied = dict(payload)
    if "children" in payload:
        copied["children"] = [copy_payload(child) for child in payload["children"]]
    return copied


def _dataframe_column_meta(column: dict[str, Any]) -> dict[str, Any]:
    """Build compact per-column metadata for tree rendering."""
    meta = {
        "null_count": column["null_count"],
        "example": column["example"],
        "python_types": column["python_types"],
    }
    if column.get("mixed_types"):
        meta["mixed_types"] = True
    return meta
