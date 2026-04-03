from __future__ import annotations

import json
import io
import importlib.util
import pickle
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from pydatapeekr import display_file, display_obj, inspect_file, inspect_obj, wrap_output


class ApiTests(unittest.TestCase):
    def test_inspect_obj_tree_shows_nested_structure(self) -> None:
        output = inspect_obj({"user": {"id": 1, "name": "Ada"}, "items": [1, "x", None]})
        self.assertIn("root: dict (2 keys)", output)
        self.assertNotIn("root: dict (2 keys)\n├── length:", output)
        self.assertIn('<key_types>: {"str": 2}', output)
        self.assertIn('"user": dict (2 keys)', output)
        self.assertIn("mixed_types: True", output)
        self.assertIn('<type_distribution>: {"NoneType": 1, "int": 1, "str": 1}', output)
        self.assertNotIn('\n    ├── length:', output)
        self.assertNotIn("<sample>:", output)

    def test_inspect_obj_shows_samples_only_when_enabled(self) -> None:
        output = inspect_obj({"count": 1, "flag": True, "name": "Ada"}, show_sample=True)
        self.assertIn("<sample>: 1", output)
        self.assertIn("<sample>: True", output)
        self.assertIn("<sample>: 'Ada'", output)

    def test_inspect_obj_markdown_returns_rendered_text(self) -> None:
        output = inspect_obj([1, "two"], format="markdown")
        self.assertIn("- **root**: list (len=2)", output)
        self.assertIn("`mixed_types`: `True`", output)

    def test_wrap_output_plain_style_returns_original_text(self) -> None:
        self.assertEqual(wrap_output("hello", style="plain"), "hello")

    def test_wrap_output_dash_style_uses_minimum_width_20(self) -> None:
        expected = "\n" + "-" * 4 + " PEEKR INFO " + "-" * 4 + "\nhello\n" + "-" * 20 + "\n"
        self.assertEqual(wrap_output("hello", style="-"), expected)

    def test_wrap_output_uses_max_line_width_and_rounds_odd_width_up(self) -> None:
        wrapped = wrap_output("123456789012345678901", style="#")
        self.assertTrue(wrapped.startswith("\n" + "#" * 5 + " PEEKR INFO " + "#" * 5 + "\n"))
        self.assertTrue(wrapped.endswith("#" * 22 + "\n"))

    def test_wrap_output_backtick_style_uses_selected_banner_character(self) -> None:
        wrapped = wrap_output("hello", style="`")
        self.assertIn("\n" + "`" * 4 + " PEEKR INFO " + "`" * 4 + "\n", wrapped)
        self.assertTrue(wrapped.endswith("`" * 20 + "\n"))

    def test_display_obj_prints_wrapped_output_without_changing_inspect_obj(self) -> None:
        buffer = io.StringIO()
        wrapped = display_obj({"a": 1}, style="-", stream=buffer)
        self.assertEqual(wrapped, buffer.getvalue())
        self.assertIn("-" * 4 + " PEEKR INFO " + "-" * 4, wrapped)
        self.assertIn("root: dict (1 keys)", wrapped)

    def test_display_file_prints_plain_output_without_wrapper(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            file_path = Path(tmp_dir) / "sample.json"
            file_path.write_text(json.dumps({"a": 1}), encoding="utf-8")
            buffer = io.StringIO()
            wrapped = display_file(file_path, style="plain", stream=buffer)
        self.assertEqual(buffer.getvalue(), wrapped)
        self.assertIn("sample.json: dict (1 keys)", wrapped)

    def test_inspect_file_json_loader(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            file_path = Path(tmp_dir) / "sample.json"
            file_path.write_text(json.dumps({"a": [1, 2, 3]}), encoding="utf-8")
            output = inspect_file(file_path, max_depth=3)
        self.assertIn("sample.json: dict (1 keys)", output)
        self.assertIn('"a": list (len=3)', output)

    def test_inspect_file_write_to_file_uses_requested_path(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            file_path = Path(tmp_dir) / "sample.json"
            output_path = Path(tmp_dir) / "report.txt"
            file_path.write_text(json.dumps({"a": 1}), encoding="utf-8")
            output = inspect_file(file_path, write_to_file=output_path)
            self.assertTrue(output_path.exists())
            self.assertEqual(output, output_path.read_text(encoding="utf-8"))

    def test_inspect_obj_write_to_file_uses_default_name_when_true(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            current = Path.cwd()
            try:
                import os

                os.chdir(tmp_dir)
                output = inspect_obj({"a": 1}, write_to_file=True)
                output_path = Path(tmp_dir) / "data_info_root.txt"
                self.assertTrue(output_path.exists())
                self.assertEqual(output, output_path.read_text(encoding="utf-8"))
            finally:
                os.chdir(current)

    def test_inspect_file_csv_loader_without_pandas_requirement(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            file_path = Path(tmp_dir) / "sample.csv"
            file_path.write_text("name,age\nAda,32\nBob,28\n", encoding="utf-8")
            output = inspect_file(file_path)
        self.assertIn("sample.csv:", output)
        self.assertTrue("len=2" in output or "DataFrame" in output)

    def test_inspect_file_yaml_loader_with_generated_data(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            file_path = Path(tmp_dir) / "sample.yaml"
            file_path.write_text(
                '{"user": {"id": 1, "name": "Ada"}, "items": [1, 2, 3]}',
                encoding="utf-8",
            )
            output = inspect_file(file_path, max_depth=3)
        self.assertIn("sample.yaml: dict (2 keys)", output)
        self.assertIn('"user": dict (2 keys)', output)
        self.assertIn('"items": list (len=3)', output)

    @unittest.skipUnless(importlib.util.find_spec("numpy"), "numpy is required for .npz loader tests")
    def test_inspect_file_npz_loader_with_generated_data(self) -> None:
        import numpy as np

        with tempfile.TemporaryDirectory() as tmp_dir:
            file_path = Path(tmp_dir) / "sample.npz"
            np.savez(
                file_path,
                states=np.array([[1.0, 2.0], [3.0, 4.0]], dtype=np.float32),
                rewards=np.array([1, 0, 1], dtype=np.int64),
            )
            output = inspect_file(file_path, max_depth=3)
        self.assertIn("sample.npz: dict (2 keys)", output)
        self.assertIn('"states": ndarray(shape=(2, 2), dtype=float32)', output)
        self.assertIn('"rewards": ndarray(shape=(3,), dtype=int64)', output)

    @unittest.skipUnless(importlib.util.find_spec("numpy"), "numpy is required for .npy loader tests")
    def test_inspect_file_npy_loader_unwraps_pickled_dict_payload(self) -> None:
        import numpy as np

        with tempfile.TemporaryDirectory() as tmp_dir:
            file_path = Path(tmp_dir) / "sample.npy"
            np.save(
                file_path,
                {
                    "observations": np.array([1.0, 2.0], dtype=np.float32),
                    "meta": {"seed": 0},
                },
                allow_pickle=True,
            )
            output = inspect_file(file_path, max_depth=3)
        self.assertIn("sample.npy: dict (2 keys)", output)
        self.assertIn('"observations": ndarray(shape=(2,), dtype=float32)', output)
        self.assertIn('"meta": dict (1 keys)', output)

    @unittest.skipUnless(importlib.util.find_spec("pyarrow"), "pyarrow is required for table inspection tests")
    def test_inspect_obj_pyarrow_table_uses_dataframe_like_column_first_view(self) -> None:
        import pyarrow as pa

        table = pa.table(
            {
                "timestamp": [0.0, 1.0, 2.0],
                "index": [10, 11, 12],
            }
        )
        output = inspect_obj(table, max_depth=3)
        self.assertIn("root: pyarrow.Table (2 columns, 3 rows)", output)
        self.assertIn('"timestamp": list (len=3)', output)
        self.assertIn("[0]: float", output)
        self.assertIn('"index": list (len=3)', output)
        self.assertIn("... 2 more item(s)", output)

    @unittest.skipUnless(importlib.util.find_spec("pandas"), "pandas is required for DataFrame inspection tests")
    def test_inspect_obj_dataframe_recurses_into_first_object_cell(self) -> None:
        import pandas as pd

        frame = pd.DataFrame(
            {
                "image": [{"bytes": b"abc", "size": [32, 32]}, {"bytes": b"def", "size": [64, 64]}],
                "label": [1, 2],
            }
        )
        output = inspect_obj(frame, max_depth=4, max_list_items=1)
        self.assertIn("root: DataFrame (2 columns, 2 rows)", output)
        self.assertIn('"image": list (len=2)', output)
        self.assertIn("[0]: dict (2 keys)", output)
        self.assertIn('"size": list (len=2)', output)
        self.assertIn('"label": list (len=2)', output)
        self.assertIn("[0]: int", output)

    @unittest.skipUnless(importlib.util.find_spec("torch"), "torch is required for tensor inspection tests")
    def test_inspect_obj_torch_tensor_shows_shape_and_dtype(self) -> None:
        import torch

        output = inspect_obj(torch.tensor([[1.0, 2.0], [3.0, 4.0]], dtype=torch.float32), max_list_items=3)
        self.assertIn("root: torch.Tensor(shape=(2, 2), dtype=torch.float32)", output)

    @unittest.skipUnless(importlib.util.find_spec("numpy"), "numpy is required for ndarray inspection tests")
    def test_inspect_obj_ndarray_does_not_show_sample_meta_by_default(self) -> None:
        import numpy as np

        output = inspect_obj(np.array([1.0, 2.0, 3.0], dtype=np.float32))
        self.assertIn("root: ndarray(shape=(3,), dtype=float32)", output)
        self.assertNotIn("shape: list", output)
        self.assertNotIn("dtype:", output)
        self.assertNotIn("<sample>:", output)

    @unittest.skipUnless(importlib.util.find_spec("numpy"), "numpy is required for ndarray inspection tests")
    def test_inspect_obj_object_ndarray_recurses_into_nested_objects(self) -> None:
        import numpy as np

        payload = np.array([{"seed": 0, "score": 1.5}], dtype=object)
        output = inspect_obj(payload, max_depth=4)
        self.assertIn("root: ndarray(shape=(1,), dtype=object)", output)
        self.assertIn("[0]: dict (2 keys)", output)
        self.assertIn('"seed": int', output)

    @unittest.skipUnless(importlib.util.find_spec("numpy"), "numpy is required for ndarray inspection tests")
    def test_inspect_obj_object_ndarray_stops_at_basic_scalar_values(self) -> None:
        import numpy as np

        payload = np.array([1, 2.5], dtype=object)
        output = inspect_obj(payload, max_depth=4, show_sample=True, max_list_items=2)
        self.assertIn("root: ndarray(shape=(2,), dtype=object)", output)
        self.assertIn("[0]: int", output)
        self.assertIn("[1]: float", output)
        self.assertIn("<sample>: 1", output)
        self.assertIn("<sample>: 2.5", output)

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

            with patch("pydatapeekr.loaders.pickle_loader.pickle.load", side_effect=ModuleNotFoundError("torch")):
                output = inspect_file(file_path)

        self.assertIn("sample.pkl: dict (2 keys)", output)
        self.assertIn('"rank": int', output)
        self.assertIn('"observations": list (len=1)', output)
        self.assertIn("[0]: dict (2 keys)", output)
        self.assertIn('"main_images": str', output)

    def test_pickle_loader_retries_with_latin1_after_unicode_decode_error(self) -> None:
        payload = {"name": "Ada", "score": 3}

        with tempfile.TemporaryDirectory() as tmp_dir:
            file_path = Path(tmp_dir) / "sample.pkl"
            with file_path.open("wb") as handle:
                pickle.dump(payload, handle, protocol=4)

            with patch(
                "pydatapeekr.loaders.pickle_loader._safe_pickle_load",
                side_effect=[UnicodeDecodeError("ascii", b"\xd5", 0, 1, "boom"), payload],
            ) as mock_load:
                output = inspect_file(file_path)

        self.assertEqual(mock_load.call_count, 2)
        self.assertEqual(mock_load.call_args_list[1].kwargs, {"encoding": "latin1"})
        self.assertIn("sample.pkl: dict (2 keys)", output)
        self.assertIn('"name": str', output)

    def test_pickle_loader_uses_static_schema_after_latin1_retry_still_needs_missing_module(self) -> None:
        payload = {
            "rank": 0,
            "observations": [{"main_images": "tensor-placeholder", "task": "demo"}],
        }

        with tempfile.TemporaryDirectory() as tmp_dir:
            file_path = Path(tmp_dir) / "sample.pkl"
            with file_path.open("wb") as handle:
                pickle.dump(payload, handle, protocol=4)

            with patch(
                "pydatapeekr.loaders.pickle_loader._safe_pickle_load",
                side_effect=[
                    UnicodeDecodeError("ascii", b"\xd5", 0, 1, "boom"),
                    ModuleNotFoundError("scipy"),
                ],
            ):
                output = inspect_file(file_path)

        self.assertIn("sample.pkl: dict (2 keys)", output)
        self.assertIn('"rank": int', output)
        self.assertIn('"observations": list (len=1)', output)

    def test_static_pickle_parser_supports_legacy_binput_memo_references(self) -> None:
        from pydatapeekr.loaders.pickle_static import inspect_pickle_structure

        # Protocol 2 emits BINPUT/BINGET opcodes.
        payload = pickle.dumps({"items": ["alpha", "beta"]}, protocol=2)
        inspection = inspect_pickle_structure(payload, root_name="sample.pkl", max_dict_items=8, max_list_items=2)

        rendered = inspection.payload
        self.assertEqual(rendered["summary"], "dict (1 keys)")
        self.assertEqual(rendered["children"][0]["name"], "items")
        self.assertEqual(rendered["children"][0]["summary"], "list (len=2)")

    def test_default_container_limits_use_dict_eight_and_list_one(self) -> None:
        payload = {f"k{index}": [index, index + 1] for index in range(10)}
        output = inspect_obj(payload)
        self.assertIn("root: dict (10 keys)", output)
        self.assertIn("... 2 more item(s)", output)
        self.assertIn('"k0": list (len=2)', output)
        self.assertIn("[0]: int", output)
        self.assertNotIn("[1]: int", output)

    def test_explicit_container_limits_override_defaults(self) -> None:
        payload = {f"k{index}": [index, index + 1, index + 2] for index in range(3)}
        output = inspect_obj(payload, max_dict_items=2, max_list_items=2)
        self.assertIn("root: dict (3 keys)", output)
        self.assertIn('"k0": list (len=3)', output)
        self.assertIn("[1]: int", output)
        self.assertIn("... 1 more item(s)", output)

    def test_dataframe_summary_uses_concise_cell_previews(self) -> None:
        from pydatapeekr.inspectors.dataframe import summarize_dataframe

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
        self.assertEqual(
            summary["column_summaries"][0]["display_type"],
            "ndarray(shape=(7,), dtype=float32)",
        )

    def test_tree_formatter_recurses_through_meta_dicts_and_lists(self) -> None:
        from pydatapeekr.formatters.tree import render_tree

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
        self.assertIn('"dtype": float32', output)
        self.assertIn("samples: list (len=2)", output)
        self.assertIn("... 1 more item(s)", output)

    def test_tree_formatter_quotes_dataframe_and_dict_keys(self) -> None:
        from pydatapeekr.formatters.tree import render_tree

        inspection = {
            "name": "frame",
            "type": "DataFrame",
            "summary": "DataFrame (1 rows, 1 columns)",
            "children": [
                {
                    "name": "observation.state",
                    "type": "dataframe_column",
                    "summary": "list (len=1)",
                    "quote_name": True,
                    "children": [
                        {
                            "name": "[0]",
                            "type": "dataframe_value",
                            "summary": "ndarray(shape=(8,), dtype=float32)",
                            "children": [],
                        }
                    ]
                }
            ],
        }

        output = render_tree(inspection)
        self.assertIn('"observation.state": list (len=1)', output)
        self.assertIn("[0]: ndarray(shape=(8,), dtype=float32)", output)

    def test_tree_formatter_places_truncated_items_after_first_child(self) -> None:
        from pydatapeekr.formatters.tree import render_tree

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

    def test_tree_formatter_renders_key_types_as_special_inline_line(self) -> None:
        from pydatapeekr.formatters.tree import render_tree

        inspection = {
            "name": "root",
            "type": "dict",
            "summary": "dict (2 keys)",
            "meta": {"key_types": {"str": 2, "int": 1}},
            "children": [],
        }

        output = render_tree(inspection)
        self.assertIn('<key_types>: {"str": 2, "int": 1}', output)
        self.assertNotIn("key_types: dict", output)

    def test_tree_formatter_renders_type_distribution_as_special_inline_line(self) -> None:
        from pydatapeekr.formatters.tree import render_tree

        inspection = {
            "name": "root",
            "type": "list",
            "summary": "list (len=2)",
            "meta": {"type_distribution": {"torch.Tensor": 2}},
            "children": [],
        }

        output = render_tree(inspection)
        self.assertIn('<type_distribution>: {"torch.Tensor": 2}', output)
        self.assertNotIn("type_distribution: dict", output)

    def test_tree_formatter_wraps_attribute_count_meta_in_angle_brackets(self) -> None:
        from pydatapeekr.formatters.tree import render_tree

        inspection = {
            "name": "cfg",
            "type": "custom_object",
            "summary": "SomeObject",
            "meta": {"attribute_count": 8},
            "children": [
                {"name": "path", "type": "list", "summary": "list (len=1)", "children": []},
            ],
        }

        output = render_tree(inspection)
        self.assertIn("<attribute_count>: 8", output)
        self.assertNotIn("attribute_count: 8", output)
        self.assertIn("path: list (len=1)", output)


if __name__ == "__main__":
    unittest.main()
