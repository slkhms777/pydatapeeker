"""Static pickle schema inspection without importing runtime dependencies."""

from __future__ import annotations

import copy
import pickletools
from dataclasses import dataclass
from typing import Any


@dataclass
class PrebuiltInspection:
    """Pre-rendered inspection tree returned by static loaders."""

    payload: dict[str, Any]


@dataclass(frozen=True)
class StaticPickleData:
    """Pickle bytes deferred for static inspection with runtime-configured limits."""

    data: bytes
    root_name: str


@dataclass(frozen=True)
class _GlobalRef:
    module: str
    name: str


_MARK = object()


def inspect_pickle_structure(
    data: bytes,
    *,
    root_name: str = "root",
    max_dict_items: int = 8,
    max_list_items: int = 1,
) -> PrebuiltInspection:
    """Parse pickle opcodes into an approximate inspection tree."""
    parser = _StaticPickleParser(max_dict_items=max_dict_items, max_list_items=max_list_items)
    parsed = parser.parse(data)
    root = parser.to_node(parsed, name=root_name)
    parser.finalize(root)
    return PrebuiltInspection(payload=root)


class _StaticPickleParser:
    def __init__(self, *, max_dict_items: int, max_list_items: int) -> None:
        self.max_dict_items = max_dict_items
        self.max_list_items = max_list_items
        self.memo: dict[int, Any] = {}
        self.next_memo_index = 0

    def parse(self, data: bytes) -> Any:
        stack: list[Any] = []
        for op, arg, _pos in pickletools.genops(data):
            name = op.name

            if name in {"PROTO", "FRAME"}:
                continue
            if name == "MARK":
                stack.append(_MARK)
            elif name == "MEMOIZE":
                self.memo[self.next_memo_index] = stack[-1]
                self.next_memo_index += 1
            elif name in {"BINGET", "LONG_BINGET"}:
                stack.append(self.memo[arg])
            elif name in {"SHORT_BINUNICODE", "BINUNICODE", "UNICODE"}:
                stack.append(arg)
            elif name in {"BININT", "BININT1", "BININT2"}:
                stack.append(arg)
            elif name == "NEWTRUE":
                stack.append(True)
            elif name == "NEWFALSE":
                stack.append(False)
            elif name == "NONE":
                stack.append(None)
            elif name in {"BINBYTES", "SHORT_BINBYTES"}:
                stack.append(b"<bytes>")
            elif name == "EMPTY_DICT":
                stack.append(self._dict_node())
            elif name == "EMPTY_LIST":
                stack.append(self._list_node())
            elif name == "EMPTY_TUPLE":
                stack.append(())
            elif name == "TUPLE":
                stack.append(tuple(self._pop_marked(stack)))
            elif name == "TUPLE1":
                stack.append((stack.pop(),))
            elif name == "TUPLE3":
                c = stack.pop()
                b = stack.pop()
                a = stack.pop()
                stack.append((a, b, c))
            elif name == "STACK_GLOBAL":
                global_name = stack.pop()
                module_name = stack.pop()
                stack.append(_GlobalRef(module=str(module_name), name=str(global_name)))
            elif name == "REDUCE":
                args = stack.pop()
                callable_ref = stack.pop()
                stack.append(self._reduce(callable_ref, args))
            elif name == "BUILD":
                state = stack.pop()
                instance = stack.pop()
                stack.append(self._build(instance, state))
            elif name == "SETITEMS":
                items = self._pop_marked(stack)
                target = stack[-1]
                self._setitems(target, items)
            elif name == "APPENDS":
                items = self._pop_marked(stack)
                target = stack[-1]
                self._appends(target, items)
            elif name == "APPEND":
                item = stack.pop()
                target = stack[-1]
                self._appends(target, [item])
            elif name == "STOP":
                return stack.pop()
            else:
                stack.append(self._opaque_node(f"unsupported opcode: {name}"))

        raise ValueError("pickle stream did not contain STOP opcode")

    def to_node(self, value: Any, *, name: str) -> dict[str, Any]:
        if self._is_node(value):
            node = copy.deepcopy(value)
            node["name"] = name
            return node
        if isinstance(value, bool):
            return {"name": name, "type": "bool", "depth": 0, "summary": "bool"}
        if isinstance(value, int):
            return {"name": name, "type": "int", "depth": 0, "summary": "int"}
        if isinstance(value, float):
            return {"name": name, "type": "float", "depth": 0, "summary": "float"}
        if isinstance(value, str):
            return {"name": name, "type": "str", "depth": 0, "summary": "str"}
        if value is None:
            return {"name": name, "type": "NoneType", "depth": 0, "summary": "NoneType"}
        if isinstance(value, bytes):
            return {"name": name, "type": "bytes", "depth": 0, "summary": "bytes"}
        if isinstance(value, tuple):
            children = [self.to_node(item, name=f"[{index}]") for index, item in enumerate(value[: self.max_list_items])]
            node = {
                "name": name,
                "type": "tuple",
                "depth": 0,
                "summary": f"tuple (len={len(value)})",
                "children": children,
            }
            if len(value) > len(children):
                node["truncated_items"] = len(value) - len(children)
            return node
        if isinstance(value, _GlobalRef):
            return {"name": name, "type": "global", "depth": 0, "summary": f"{value.module}.{value.name}"}
        return {"name": name, "type": type(value).__name__, "depth": 0, "summary": type(value).__name__}

    def finalize(self, node: dict[str, Any], *, depth: int = 0) -> None:
        node["depth"] = depth
        node.pop("_kind", None)
        node.pop("_child_count", None)
        node.pop("_item_count", None)
        for child in node.get("children", []):
            self.finalize(child, depth=depth + 1)

    def _reduce(self, callable_ref: Any, args: Any) -> Any:
        if callable_ref == _GlobalRef("torch._utils", "_rebuild_tensor_v2"):
            return self._opaque_node("torch tensor")
        if callable_ref == _GlobalRef("torch.storage", "_load_from_bytes"):
            return self._opaque_node("torch storage")
        if callable_ref == _GlobalRef("numpy.core.multiarray", "_reconstruct"):
            return self._opaque_node("numpy.ndarray")
        if callable_ref == _GlobalRef("numpy", "dtype"):
            return self._opaque_node("numpy dtype")
        if callable_ref == _GlobalRef("collections", "OrderedDict"):
            return self._dict_node(summary="OrderedDict")
        if isinstance(callable_ref, _GlobalRef):
            return self._opaque_node(f"{callable_ref.module}.{callable_ref.name}")
        return self._opaque_node("reduced object")

    def _build(self, instance: Any, _state: Any) -> Any:
        return instance

    def _setitems(self, target: Any, items: list[Any]) -> None:
        if not self._is_node(target) or target.get("_kind") != "dict":
            return
        for index in range(0, len(items), 2):
            key = items[index]
            value = items[index + 1]
            target["_item_count"] += 1
            if len(target["children"]) < self.max_dict_items:
                child = self.to_node(value, name=str(key))
                child["quote_name"] = True
                target["children"].append(child)
        self._refresh_dict_summary(target)

    def _appends(self, target: Any, items: list[Any]) -> None:
        if not self._is_node(target) or target.get("_kind") != "list":
            return
        for item in items:
            target["_item_count"] += 1
            if len(target["children"]) < self.max_list_items:
                index = len(target["children"])
                target["children"].append(self.to_node(item, name=f"[{index}]"))
        self._refresh_list_summary(target)

    def _pop_marked(self, stack: list[Any]) -> list[Any]:
        items: list[Any] = []
        while stack:
            current = stack.pop()
            if current is _MARK:
                break
            items.append(current)
        items.reverse()
        return items

    def _dict_node(self, *, summary: str = "dict") -> dict[str, Any]:
        return {
            "name": "",
            "type": "dict",
            "depth": 0,
            "summary": summary,
            "children": [],
            "_kind": "dict",
            "_label": summary,
            "_item_count": 0,
        }

    def _list_node(self) -> dict[str, Any]:
        return {
            "name": "",
            "type": "list",
            "depth": 0,
            "summary": "list (len=0)",
            "children": [],
            "_kind": "list",
            "_item_count": 0,
        }

    def _opaque_node(self, summary: str) -> dict[str, Any]:
        return {"name": "", "type": summary, "depth": 0, "summary": summary}

    def _refresh_list_summary(self, node: dict[str, Any]) -> None:
        count = node.get("_item_count", len(node.get("children", [])))
        node["summary"] = f"list (len={count})"
        hidden = count - len(node.get("children", []))
        if hidden > 0:
            node["truncated_items"] = hidden
        elif "truncated_items" in node:
            node.pop("truncated_items")

    def _refresh_dict_summary(self, node: dict[str, Any]) -> None:
        label = node.get("_label", "dict")
        count = node.get("_item_count", len(node.get("children", [])))
        node["summary"] = f"{label} ({count} keys)"
        hidden = count - len(node.get("children", []))
        if hidden > 0:
            node["truncated_items"] = hidden
        elif "truncated_items" in node:
            node.pop("truncated_items")

    def _is_node(self, value: Any) -> bool:
        return isinstance(value, dict) and "summary" in value and "type" in value
