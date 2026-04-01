# PyDataPeekr

PyDataPeekr is a Python tool for inspecting nested data files and complex in-memory objects with readable tree and Markdown output.

Chinese README: [docs/README_zh.md](docs/README_zh.md)

## Supported File Extensions

`*.pkl` `*.pickle` `*.parquet` `*.json` `*.jsonl` `*.csv` `*.tsv` `*.yaml` `*.yml` `*.npy` `*.npz`

## Installation

Install directly from PyPI:

```bash
pip install pydatapeekr
# or
uv pip install pydatapeekr
```

For local development:

```bash
git clone https://github.com/slkhms777/pydatapeekr.git
cd pydatapeekr
pip install -e .
```

## CLI Usage

Quick Start:

```bash
pydatapeekr your_file_path
```

Show all CLI options:

```bash
pydatapeekr --help
```

Common example:

```bash
pydatapeekr your_file.parquet --max-depth 4 --max-dict-items 8 --max-list-items 1
```

Supported CLI parameters:

- `path`
  Input file path.
- `--max-depth`
  Maximum recursion depth. Default: `4`.
- `--max-dict-items`
  Maximum displayed entries for dict-like nodes. Default: `8`.
- `--max-list-items`
  Maximum displayed entries for list-like nodes. Default: `1`.
- `--show-sample`
  Show sample values for primitive leaf types. Default: `False`.
- `--format`
  Output format: `tree` or `markdown`. Default: `tree`.
- `--write-to-file [OUTPUT_PATH]`
  Write the result to a file. Default filename: `data_info_{file_name}.txt`. Supported suffixes: `.txt`, `.md`, `.markdown`.

## API Usage

```python
from pydatapeekr import inspect_file, inspect_obj

text = inspect_file(
    "data.json",
    max_depth=4,
    max_dict_items=8,
    max_list_items=1,
    show_sample=False,
    format="tree",
    write_to_file=None,
)

markdown_text = inspect_obj(
    {"user": {"id": 1}, "items": [1, 2, 3]},
    max_depth=4,
    max_dict_items=8,
    max_list_items=1,
    show_sample=True,
    format="markdown",
    write_to_file="report.md",
)
```
