# DataLens

DataLens 是一个用于探查嵌套数据文件和复杂 Python 对象结构的工具，支持清晰的树状输出和 Markdown 输出。

English README: [../README.md](../README.md)

## 1. 支持的文件后缀

`*.pkl` `*.pickle` `*.parquet` `*.json` `*.jsonl` `*.csv` `*.tsv` `*.yaml` `*.yml` `*.npy` `*.npz`

## 2. 安装方式

```bash
git clone https://github.com/slkhms777/DataLens.git
cd DataLens
pip install -e .
```

## 3. CLI 用法

查看完整帮助：

```bash
datalens --help
```

常用示例：

```bash
datalens your_file.parquet --max-depth 4 --max-dict-items 8 --max-list-items 1
```

支持的 CLI 参数：

- `path`
  输入文件路径。
- `--max-depth`
  最大递归深度，默认 `4`。
- `--max-dict-items`
  每个 `dict` 类节点最多展示多少个 key，默认 `8`。
- `--max-list-items`
  每个 `list` 类节点最多展示多少个元素，默认 `1`。
- `--show-sample`
  显示基础类型的示例值，默认关闭。
- `--format`
  输出格式，仅支持 `tree` 和 `markdown`，默认 `tree`。
- `--write-to-file [OUTPUT_PATH]`
  将结果写入文件。默认文件名为 `data_info_{file_name}.txt`。仅支持 `.txt`、`.md`、`.markdown`。

## 4. API 用法

```python
from datalens import inspect_file, inspect_obj

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
