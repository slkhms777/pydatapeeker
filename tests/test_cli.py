from __future__ import annotations

import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

import json


class CliTests(unittest.TestCase):
    def test_cli_tree_output(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            file_path = Path(tmp_dir) / "data.json"
            file_path.write_text(json.dumps({"x": [1, 2]}), encoding="utf-8")
            result = subprocess.run(
                [sys.executable, "-m", "datalens.cli", str(file_path)],
                capture_output=True,
                text=True,
                check=False,
            )
        self.assertEqual(result.returncode, 0)
        self.assertIn("data.json: dict (1 keys)", result.stdout)

    def test_cli_markdown_output(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            file_path = Path(tmp_dir) / "data.json"
            file_path.write_text(json.dumps({"x": [1, "two"]}), encoding="utf-8")
            result = subprocess.run(
                [sys.executable, "-m", "datalens.cli", str(file_path), "--format", "markdown"],
                capture_output=True,
                text=True,
                check=False,
            )
        self.assertEqual(result.returncode, 0)
        self.assertIn("- **data.json**: dict (1 keys)", result.stdout)

    def test_cli_sample_flag_enables_basic_leaf_samples(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            file_path = Path(tmp_dir) / "data.json"
            file_path.write_text(json.dumps({"x": 1, "y": True}), encoding="utf-8")
            result = subprocess.run(
                [sys.executable, "-m", "datalens.cli", str(file_path), "--show-sample"],
                capture_output=True,
                text=True,
                check=False,
            )
        self.assertEqual(result.returncode, 0)
        self.assertIn("<sample>: 1", result.stdout)
        self.assertIn("<sample>: True", result.stdout)

    def test_cli_help_shows_supported_parameters(self) -> None:
        result = subprocess.run(
            [sys.executable, "-m", "datalens.cli", "--help"],
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(result.returncode, 0)
        self.assertIn("--max-depth", result.stdout)
        self.assertIn("--max-dict-items", result.stdout)
        self.assertIn("--max-list-items", result.stdout)
        self.assertIn("--show-sample", result.stdout)
        self.assertIn("--format", result.stdout)
        self.assertIn("--write-to-file", result.stdout)
        self.assertIn("default:", result.stdout.lower())

    def test_cli_dict_and_list_item_flags_override_defaults(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            file_path = Path(tmp_dir) / "data.json"
            file_path.write_text(json.dumps({"a": [1, 2, 3], "b": [4, 5, 6], "c": [7, 8, 9]}), encoding="utf-8")
            result = subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "datalens.cli",
                    str(file_path),
                    "--max-dict-items",
                    "2",
                    "--max-list-items",
                    "2",
                ],
                capture_output=True,
                text=True,
                check=False,
            )
        self.assertEqual(result.returncode, 0)
        self.assertIn('"a": list (len=3)', result.stdout)
        self.assertIn("[1]: int", result.stdout)
        self.assertIn("... 1 more item(s)", result.stdout)

    def test_cli_write_to_file_uses_default_name(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            file_path = Path(tmp_dir) / "data.json"
            file_path.write_text(json.dumps({"x": 1}), encoding="utf-8")
            result = subprocess.run(
                [sys.executable, "-m", "datalens.cli", str(file_path), "--write-to-file"],
                capture_output=True,
                text=True,
                check=False,
            )
            output_file = Path(tmp_dir) / "data_info_data.json.txt"
            self.assertEqual(result.returncode, 0)
            self.assertTrue(output_file.exists())
            self.assertIn("data.json: dict (1 keys)", output_file.read_text(encoding="utf-8"))

    def test_cli_write_to_file_accepts_markdown_extension(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            file_path = Path(tmp_dir) / "data.json"
            output_path = Path(tmp_dir) / "report.md"
            file_path.write_text(json.dumps({"x": [1, 2]}), encoding="utf-8")
            result = subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "datalens.cli",
                    str(file_path),
                    "--format",
                    "markdown",
                    "--write-to-file",
                    str(output_path),
                ],
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(result.returncode, 0)
            self.assertTrue(output_path.exists())
            self.assertIn("- **data.json**: dict (1 keys)", output_path.read_text(encoding="utf-8"))

    def test_cli_write_to_file_rejects_unsupported_suffix(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            file_path = Path(tmp_dir) / "data.json"
            file_path.write_text(json.dumps({"x": 1}), encoding="utf-8")
            result = subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "datalens.cli",
                    str(file_path),
                    "--write-to-file",
                    str(Path(tmp_dir) / "report.json"),
                ],
                capture_output=True,
                text=True,
                check=False,
            )
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("Output file must use one of", result.stderr)


if __name__ == "__main__":
    unittest.main()
