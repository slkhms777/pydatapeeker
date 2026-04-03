# API Guide

## Quick Start

```python
import pydatapeekr as peekr

print(peekr.inspect_file("data.json"))
```

## Core Functions

### `peekr.inspect_file(...)`

Inspect a file and return rendered text.

```python
import pydatapeekr as peekr

text = peekr.inspect_file(
    "data.json",
    max_depth=4,
    max_dict_items=8,
    max_list_items=1,
    show_sample=False,
    format="tree",
    write_to_file=None,
)
```

### `peekr.inspect_obj(...)`

Inspect an in-memory object and return rendered text.

```python
import pydatapeekr as peekr

text = peekr.inspect_obj(
    {"user": {"id": 1}, "items": [1, 2, 3]},
    max_depth=4,
    max_dict_items=8,
    max_list_items=1,
    show_sample=True,
    format="markdown",
    write_to_file="report.md",
)
```

### `peekr.display_file(...)`

Print a file inspection result with a terminal-friendly wrapper.

```python
import pydatapeekr as peekr

peekr.display_file("data.json")  # default style="-"
```

### `peekr.display_obj(...)`

Print an object inspection result with a terminal-friendly wrapper.

```python
import pydatapeekr as peekr

peekr.display_obj(
    {"user": {"id": 1}, "items": [1, 2, 3]},
    style="#",
)
```

## Display Styles

- `plain`: no wrapper
- `-`: dashed banner wrapper, with blank lines before and after
- `#`: hash banner wrapper, with blank lines before and after
- `` ` ``: backtick banner wrapper, with blank lines before and after

## Common Parameters

- `max_depth`: maximum recursion depth, default `4`
- `max_dict_items`: maximum displayed entries for dict-like nodes, default `8`
- `max_list_items`: maximum displayed entries for list-like nodes, default `1`
- `show_sample`: include sample values for primitive leaf types
- `format`: `tree` or `markdown`
- `write_to_file`: write output to `.txt`, `.md`, or `.markdown`
