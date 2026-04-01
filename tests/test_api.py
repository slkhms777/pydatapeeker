from __future__ import annotations

import json
import pickle
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from datalens import inspect_file, inspect_obj


class ApiTests(unittest.TestCase):
    def test_inspect_obj_tree_shows_nested_structure(self) -> None:
        output = inspect_obj({"user": {"id": 1, "name": "Ada"}, "items": [1, "x", None]})
        self.assertIn("root: dict (2 keys)", output)
        self.assertIn("user: dict (2 keys)", output)
        self.assertIn("mixed_types: True", output)

    def test_inspect_obj_json_returns_serialized_payload(self) -> None:
        output = inspect_obj([1, "two"], format="json")
        payload = json.loads(output)
        self.assertEqual(payload["summary"], "list (len=2)")
        self.assertTrue(payload["meta"]["mixed_types"])

    def test_inspect_file_json_loader(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            file_path = Path(tmp_dir) / "sample.json"
            file_path.write_text(json.dumps({"a": [1, 2, 3]}), encoding="utf-8")
            output = inspect_file(file_path, max_depth=3)
        self.assertIn("sample.json: dict (1 keys)", output)
        self.assertIn("a: list (len=3)", output)

    def test_inspect_file_csv_loader_without_pandas_requirement(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            file_path = Path(tmp_dir) / "sample.csv"
            file_path.write_text("name,age\nAda,32\nBob,28\n", encoding="utf-8")
            output = inspect_file(file_path)
        self.assertIn("sample.csv:", output)
        self.assertTrue("len=2" in output or "DataFrame" in output)

    def test_max_depth_stops_recursion(self) -> None:
        output = inspect_obj({"a": {"b": {"c": 1}}}, max_depth=2)
        self.assertIn("max depth reached", output)

    def test_circular_reference_is_detected_without_false_positive_on_shared_object(self) -> None:
        shared = {"value": 1}
        payload = {"left": shared, "right": shared}
        output = inspect_obj(payload, max_depth=4)
        self.assertNotIn("circular reference", output)

        cycle: dict[str, object] = {}
        cycle["self"] = cycle
        cycle_output = inspect_obj(cycle, max_depth=4)
        self.assertIn("circular reference", cycle_output)

    def test_pickle_loader_falls_back_to_static_schema_when_import_is_missing(self) -> None:
        payload = {
            "rank": 0,
            "observations": [{"main_images": "tensor-placeholder", "task": "demo"}],
        }
        with tempfile.TemporaryDirectory() as tmp_dir:
            file_path = Path(tmp_dir) / "sample.pkl"
            with file_path.open("wb") as handle:
                pickle.dump(payload, handle, protocol=4)

            with patch("datalens.loaders.pickle_loader.pickle.load", side_effect=ModuleNotFoundError("torch")):
                output = inspect_file(file_path)

        self.assertIn("sample.pkl: dict (2 keys)", output)
        self.assertIn("rank: int", output)
        self.assertIn("observations: list (len=1)", output)
        self.assertIn("[0]: dict (2 keys)", output)
        self.assertIn("main_images: str", output)

    def test_dataframe_summary_uses_concise_cell_previews(self) -> None:
        from datalens.inspectors.dataframe import summarize_dataframe

        class FakeSeries:
            def __init__(self, values):
                self._values = values
                self.iloc = self

            def head(self, count):
                return FakeSeries(self._values[:count])

            def tolist(self):
                return list(self._values)

            def __getitem__(self, index):
                return self._values[index]

            def __len__(self):
                return len(self._values)

        class FakeNullSum:
            def __init__(self, mapping):
                self._mapping = mapping

            def items(self):
                return self._mapping.items()

        class FakeDTypes:
            def __init__(self, mapping):
                self._mapping = mapping

            def items(self):
                return self._mapping.items()

        class FakeHead:
            def __init__(self, rows):
                self._rows = rows

            def to_dict(self, orient="records"):
                return list(self._rows)

        class FakeArray:
            __module__ = "numpy"

            def __init__(self, shape, dtype):
                self.shape = shape
                self.dtype = dtype

            def __repr__(self):
                return "FakeArray([1, 2, 3, 4, 5, 6])"

        class FakeDF:
            def __init__(self):
                self.columns = ["observation.state", "frame_index"]
                self.dtypes = FakeDTypes({"observation.state": "object", "frame_index": "int64"})
                self.shape = (2, 2)
                self._rows = [
                    {"observation.state": FakeArray((7,), "float32"), "frame_index": 0},
                    {"observation.state": FakeArray((7,), "float32"), "frame_index": 1},
                ]
                self._series = {
                    "observation.state": FakeSeries([row["observation.state"] for row in self._rows]),
                    "frame_index": FakeSeries([row["frame_index"] for row in self._rows]),
                }

            def head(self, count):
                return FakeHead(self._rows[:count])

            def isnull(self):
                class FakeNullFrame:
                    def sum(self_inner):
                        return FakeNullSum({"observation.state": 0, "frame_index": 0})

                return FakeNullFrame()

            def __getitem__(self, key):
                return self._series[key]

        summary = summarize_dataframe(FakeDF(), max_items=2)
        self.assertEqual(
            summary["column_examples"]["observation.state"],
            "ndarray(shape=(7,), dtype=float32)",
        )
        self.assertEqual(
            summary["sample_rows"][0]["observation.state"],
            "ndarray(shape=(7,), dtype=float32)",
        )
        self.assertEqual(summary["column_count"], 2)
        self.assertEqual(summary["column_summaries"][0]["name"], "observation.state")
        self.assertEqual(summary["column_summaries"][0]["dtype"], "object")

    def test_tree_formatter_recurses_through_meta_dicts_and_lists(self) -> None:
        from datalens.formatters.tree import render_tree

        inspection = {
            "name": "root",
            "type": "custom",
            "summary": "custom",
            "meta": {
                "shape": [138, 7],
                "details": {"dtype": "float32", "count": 3},
                "samples": [{"a": 1}, {"a": 2}],
            },
            "children": [],
        }

        output = render_tree(inspection)
        self.assertIn("shape: list (len=2)", output)
        self.assertIn("details: dict (2 keys)", output)
        self.assertIn("dtype: float32", output)
        self.assertIn("samples: list (len=2)", output)
        self.assertIn("... 1 more item(s)", output)

    def test_tree_formatter_places_truncated_items_after_first_child(self) -> None:
        from datalens.formatters.tree import render_tree

        inspection = {
            "name": "root",
            "type": "list",
            "summary": "list (len=3)",
            "children": [
                {"name": "[0]", "type": "int", "summary": "int", "children": []},
            ],
            "truncated_items": 2,
        }

        output = render_tree(inspection)
        self.assertLess(output.index("[0]: int"), output.index("... 2 more item(s)"))


if __name__ == "__main__":
    unittest.main()
