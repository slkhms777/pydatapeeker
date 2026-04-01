# DataLens

DataLens 是一个面向复杂数据结构的 Python 数据探查与类型检查工具，适合在数据清洗、调试、EDA 和 pipeline 验证阶段快速查看文件结构、字段类型与嵌套关系。

## 功能特性

- 自动加载多种常见格式：`pkl`、`parquet`、`json`、`jsonl`、`csv`、`tsv`
- 递归分析 `dict`、`list`、`tuple`、`set`、`DataFrame`、`ndarray` 等对象
- 支持树状输出、JSON 输出和 Markdown 输出
- 支持 `max_depth` / `max_items`，避免一次性打印过多内容
- 检测列表和列中的混合类型
- 对 `pickle` 提供安全警告
- 当 `pickle` 依赖缺失模块时，支持静态结构探查降级输出

## 安装

建议在虚拟环境中安装：

```bash
pip install -e .
```

如果你只想在当前项目里运行，也可以直接使用：

```bash
./.venv/bin/python -m datalens.cli your_file.json
```

## 命令行使用

默认输出为树状结构：

```bash
datalens data.json
datalens data.parquet --depth 3 --items 5
datalens data.csv --format json
```

常用参数：

- `--depth`：最大递归深度
- `--items`：每层最多展示多少个元素
- `--format`：输出格式，可选 `tree`、`json`、`md`、`markdown`

## Python API

```python
from datalens import inspect_file, inspect_obj

print(inspect_file("data.json"))

data = {
    "user": {"id": 1, "name": "Ada"},
    "items": [1, "x", None],
}
print(inspect_obj(data, max_depth=3, max_items=3))
```

## 输出风格

DataLens 的树状输出遵循以下规则：

- 对字典类对象，逐个展开每个 key
- 对列表、元组、数组等序列对象，只展示一个示例元素
- 其余元素使用 `... N more item(s)` 省略
- 对嵌套结构继续递归展开

示例：

```text
root: dict (3 keys)
├── user: dict (2 keys)
│   ├── id: int
│   └── name: str
└── items: list (len=2)
    ├── [0]: int
    └── ... 1 more item(s)
```

## 开发与测试

运行单元测试：

```bash
python3 -m unittest discover -s tests -v
```

如果项目已经有 `.venv` 环境，也可以使用：

```bash
./.venv/bin/python -m unittest discover -s tests -v
```

## 注意事项

- `pickle` 文件可能执行任意代码，只应加载可信文件
- 对于依赖外部模块的 `pickle`，若当前环境缺少对应模块，DataLens 会退化为静态 schema 探查模式
- 大型样例数据建议不要直接提交到 GitHub 仓库

