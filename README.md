# PyDataPeekr

PyDataPeekr is a Python tool for inspecting nested data files and complex in-memory objects with readable tree and Markdown output. It helps you debug data structure types directly in the terminal, and it also gives agents a fast way to inspect the contents and schema of otherwise hard-to-read or invisible data files.

[Full API guide](docs/api.md)

[README（中文版）](docs/README_zh.md)
[API (中文版)](docs/api_zh.md)

## Supported File Extensions

`*.pkl` `*.pickle` `*.parquet` `*.json` `*.jsonl` `*.csv` `*.tsv` `*.yaml` `*.yml` `*.npy` `*.npz`

## Installation

Stable release from PyPI:

```bash
pip install pydatapeekr
# or
uv pip install pydatapeekr
```

Latest version from the repository (`beta`, may be unstable):

```bash
pip install "git+https://github.com/slkhms777/pydatapeekr.git"
# or
uv pip install "git+https://github.com/slkhms777/pydatapeekr.git"
```

## CLI Usage

Quick Start:

```bash
peek your_file_path
```

## API Usage

```python
import pydatapeekr as peekr

# Get rendered text from a file or Python object.
file_text = peekr.inspect_file("data.parquet")
obj_text = peekr.inspect_obj(
    {"user": {"id": 1}, "items": [1, 2, 3]},  # or any Python object
    format="markdown",
)

print(file_text)
print(obj_text)

# Print directly with a terminal-friendly wrapper.
peekr.display_file("data.parquet")  # default style="-"
peekr.display_obj(
    your_object,
    style="#",
)
```

For the full API reference and more examples, see [docs/api.md](docs/api.md).

## Examples

### Case 1: Inspect an In-Memory Object

```python
import pydatapeekr as peekr

# Suppose `raw_image_data` is an intermediate DataFrame variable.
peekr.display_obj(raw_image_data, style="-")
```

Terminal output:

```text
------------- PEEKR INFO -------------
root: DataFrame (2 columns, 2500 rows)
├── "image": list (len=2500)
│   ├── [0]: dict (2 keys)
│   │   ├── <key_types>: {"str": 2}
│   │   ├── "bytes": bytes
│   │   └── "path": str
│   └── ... 2499 more item(s)
└── "label": list (len=2500)
    ├── [0]: numpy.int64
    └── ... 2499 more item(s)
--------------------------------------
```

### Case 2: Inspect a Data File

```python
import pydatapeekr as peekr

# Example file:
# https://huggingface.co/datasets/timm/mini-imagenet/tree/main/data
peekr.display_file("test-00000-of-00002.parquet", style="-")
```

Terminal output:

```text
------------------------- PEEKR INFO -------------------------
test-00000-of-00002.parquet: DataFrame (2 columns, 2500 rows)
├── "image": list (len=2500)
│   ├── [0]: dict (2 keys)
│   │   ├── <key_types>: {"str": 2}
│   │   ├── "bytes": bytes
│   │   └── "path": str
│   └── ... 2499 more item(s)
└── "label": list (len=2500)
    ├── [0]: numpy.int64
    └── ... 2499 more item(s)
--------------------------------------------------------------
```
