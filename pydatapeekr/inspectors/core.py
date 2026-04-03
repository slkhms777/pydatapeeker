"""Recursive object analysis."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any

from pydatapeekr.inspectors.dataframe import summarize_dataframe
from pydatapeekr.inspectors.ndarray import ndarray_display_type
from pydatapeekr.inspectors.table import summarize_table
from pydatapeekr.inspectors.tensor import tensor_display_type
from pydatapeekr.loaders.pickle_static import PrebuiltInspection, StaticPickleData, inspect_pickle_structure
from pydatapeekr.utils import distribution, safe_repr, truncate_mapping_items, truncate_sequence_items, type_name


def analyze_object(
    obj: Any,
    *,
    name: str = "root",
    max_depth: int = 4,
    max_dict_items: int = 8,
    max_list_items: int = 1,
    show_sample: bool = False,
) -> dict[str, Any]:
    """Analyze any supported Python object into a serializable tree."""
    if isinstance(obj, StaticPickleData):
        payload = inspect_pickle_structure(
            obj.data,
            root_name=name or obj.root_name,
            max_dict_items=max_dict_items,
            max_list_items=max_list_items,
        ).payload
        return payload
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
        max_dict_items=max_dict_items,
        max_list_items=max_list_items,
        show_sample=show_sample,
        active_path=active_path,
    )


def _analyze(
    obj: Any,
    *,
    name: str,
    depth: int,
    max_depth: int,
    max_dict_items: int,
    max_list_items: int,
    show_sample: bool,
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
            if show_sample and _is_sample_type(obj):
                node["sample"] = safe_repr(obj)
            return node

        dataframe_type = _import_type("pandas", "DataFrame")
        table_type = _import_type("pyarrow", "Table")
        ndarray_type = _import_type("numpy", "ndarray")
        tensor_type = _import_type("torch", "Tensor")

        if dataframe_type is not None and isinstance(obj, dataframe_type):
            summary = summarize_dataframe(obj, max_items=max_list_items)
            row_count, column_count = summary["shape"]
            node["summary"] = f"DataFrame ({column_count} columns, {row_count} rows)"
            node["children"] = [
                _analyze_tabular_column(
                    value=obj[column["name"]].iloc[0] if row_count > 0 else None,
                    name=column["name"],
                    column_type="dataframe_column",
                    row_count=row_count,
                    depth=depth,
                    max_depth=max_depth,
                    max_dict_items=max_dict_items,
                    max_list_items=max_list_items,
                    show_sample=show_sample,
                    active_path=active_path,
                )
                for column in summary.get("column_summaries", [])
            ]
            return node

        if table_type is not None and isinstance(obj, table_type):
            summary = summarize_table(obj)
            row_count, column_count = summary["shape"]
            node["summary"] = f"pyarrow.Table ({column_count} columns, {row_count} rows)"
            node["children"] = [
                {
                    "name": column["name"],
                    "type": "pyarrow_column",
                    "depth": depth + 1,
                    "summary": f"list (len={row_count})",
                    "quote_name": True,
                    "children": (
                        [
                            {
                                "name": "[0]",
                                "type": "pyarrow_value",
                                "depth": depth + 2,
                                "summary": column["display_type"],
                            }
                        ]
                        if row_count > 0
                        else []
                    ),
                    **({"truncated_items": row_count - 1} if row_count > 1 else {}),
                }
                for column in summary.get("column_summaries", [])
            ]
            return node

        if ndarray_type is not None and isinstance(obj, ndarray_type):
            node["summary"] = ndarray_display_type(obj)
            if str(getattr(obj, "dtype", "")) == "object":
                _attach_object_array_children(
                    obj,
                    node=node,
                    depth=depth,
                    max_depth=max_depth,
                    max_dict_items=max_dict_items,
                    max_list_items=max_list_items,
                    show_sample=show_sample,
                    active_path=active_path,
                )
            return node

        if tensor_type is not None and isinstance(obj, tensor_type):
            node["summary"] = tensor_display_type(obj)
            return node

        if isinstance(obj, Mapping):
            return _analyze_mapping(
                obj,
                node=node,
                depth=depth,
                max_depth=max_depth,
                max_dict_items=max_dict_items,
                max_list_items=max_list_items,
                show_sample=show_sample,
                active_path=active_path,
            )

        if isinstance(obj, (list, tuple, set)):
            return _analyze_sequence(
                obj,
                node=node,
                depth=depth,
                max_depth=max_depth,
                max_dict_items=max_dict_items,
                max_list_items=max_list_items,
                show_sample=show_sample,
                active_path=active_path,
            )

        if _is_basic_type(obj):
            node["summary"] = type_name(obj)
            if show_sample and _is_sample_type(obj):
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
                    max_dict_items=max_dict_items,
                    max_list_items=max_list_items,
                    show_sample=show_sample,
                    active_path=active_path,
                )
                for key, value in list(attrs.items())[:max_dict_items]
            ]
            hidden = max(len(attrs) - len(node["children"]), 0)
            if hidden:
                node["truncated_items"] = hidden
            return node

        node["summary"] = type_name(obj)
        if show_sample and _is_sample_type(obj):
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
    max_dict_items: int,
    max_list_items: int,
    show_sample: bool,
    active_path: set[int],
) -> dict[str, Any]:
    items = list(obj.items())
    shown, hidden = truncate_mapping_items(items, max_dict_items)
    node["summary"] = f"dict ({len(obj)} keys)"
    node["meta"] = {"key_types": distribution(obj.keys())}
    node["children"] = [
        _mark_quoted_name(
            _analyze(
                value,
                name=str(key),
                depth=depth + 1,
                max_depth=max_depth,
                max_dict_items=max_dict_items,
                max_list_items=max_list_items,
                show_sample=show_sample,
                active_path=active_path,
            )
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
    max_dict_items: int,
    max_list_items: int,
    show_sample: bool,
    active_path: set[int],
) -> dict[str, Any]:
    sequence = list(obj)
    shown, hidden = truncate_sequence_items(sequence, max_list_items)
    type_counts = distribution(sequence)
    node["summary"] = f"{type(obj).__name__} (len={len(sequence)})"
    node["meta"] = {
        "type_distribution": type_counts,
        "mixed_types": len(type_counts) > 1,
    }
    node["children"] = [
        _analyze(
            value,
            name=f"[{index}]",
            depth=depth + 1,
            max_depth=max_depth,
            max_dict_items=max_dict_items,
            max_list_items=max_list_items,
            show_sample=show_sample,
            active_path=active_path,
        )
        for index, value in enumerate(shown)
    ]
    if hidden:
        node["truncated_items"] = hidden
    return node


def _attach_object_array_children(
    obj: Any,
    *,
    node: dict[str, Any],
    depth: int,
    max_depth: int,
    max_dict_items: int,
    max_list_items: int,
    show_sample: bool,
    active_path: set[int],
) -> None:
    """Recursively inspect object-dtype ndarray elements."""
    shape = getattr(obj, "shape", ())
    if shape == ():
        value = obj.item()
        if _is_basic_type(value):
            return
        node["children"] = [
            _analyze(
                value,
                name="value",
                depth=depth + 1,
                max_depth=max_depth,
                max_dict_items=max_dict_items,
                max_list_items=max_list_items,
                show_sample=show_sample,
                active_path=active_path,
            )
        ]
        return

    shown, hidden = truncate_sequence_items(list(obj), max_list_items)
    children = []
    for index, value in enumerate(shown):
        children.append(
            _analyze(
                value,
                name=f"[{index}]",
                depth=depth + 1,
                max_depth=max_depth,
                max_dict_items=max_dict_items,
                max_list_items=max_list_items,
                show_sample=show_sample,
                active_path=active_path,
            )
        )

    if children:
        node["children"] = children
    if hidden:
        node["truncated_items"] = hidden


def _analyze_tabular_column(
    value: Any,
    *,
    name: str,
    column_type: str,
    row_count: int,
    depth: int,
    max_depth: int,
    max_dict_items: int,
    max_list_items: int,
    show_sample: bool,
    active_path: set[int],
) -> dict[str, Any]:
    """Represent a tabular column as a list whose first item is recursively analyzed."""
    node: dict[str, Any] = {
        "name": name,
        "type": column_type,
        "depth": depth + 1,
        "summary": f"list (len={row_count})",
        "quote_name": True,
        "children": [],
    }
    if row_count > 0:
        node["children"] = [
            _analyze(
                value,
                name="[0]",
                depth=depth + 2,
                max_depth=max_depth,
                max_dict_items=max_dict_items,
                max_list_items=max_list_items,
                show_sample=show_sample,
                active_path=active_path,
            )
        ]
    if row_count > 1:
        node["truncated_items"] = row_count - 1
    return node


def _is_basic_type(obj: Any) -> bool:
    return isinstance(obj, (str, int, float, bool, type(None), bytes))


def _is_sample_type(obj: Any) -> bool:
    return isinstance(obj, (str, int, float, bool, type(None)))


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


def _mark_quoted_name(node: dict[str, Any]) -> dict[str, Any]:
    """Mark a node so its displayed name is rendered with double quotes."""
    node["quote_name"] = True
    return node
