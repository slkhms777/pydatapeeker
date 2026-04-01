from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


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

    def test_cli_json_output(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            file_path = Path(tmp_dir) / "data.json"
            file_path.write_text(json.dumps({"x": [1, "two"]}), encoding="utf-8")
            result = subprocess.run(
                [sys.executable, "-m", "datalens.cli", str(file_path), "--format", "json"],
                capture_output=True,
                text=True,
                check=False,
            )
        self.assertEqual(result.returncode, 0)
        payload = json.loads(result.stdout)
        self.assertEqual(payload["name"], "data.json")


if __name__ == "__main__":
    unittest.main()
