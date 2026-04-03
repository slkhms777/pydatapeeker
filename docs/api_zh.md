# API 文档

## 快速开始

```python
import pydatapeekr as peekr

print(peekr.inspect_file("data.json"))
```

## 核心函数

### `peekr.inspect_file(...)`

探查文件并返回渲染后的文本。

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

探查内存中的 Python 对象并返回渲染后的文本。

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

为终端输出添加外壳后，直接打印文件探查结果。

```python
import pydatapeekr as peekr

peekr.display_file("data.json")  # 默认 style="-"
```

### `peekr.display_obj(...)`

为终端输出添加外壳后，直接打印对象探查结果。

```python
import pydatapeekr as peekr

peekr.display_obj(
    {"user": {"id": 1}, "items": [1, 2, 3]},
    style="#",
)
```

## 输出外壳样式

- `plain`：不加额外外壳
- `-`：使用横线标题栏外壳，前后自带空行
- `#`：使用井号标题栏外壳，前后自带空行
- `` ` ``：使用反引号标题栏外壳，前后自带空行

## 常用参数

- `max_depth`：最大递归深度，默认 `4`
- `max_dict_items`：每个 `dict` 类节点最多展示多少个条目，默认 `8`
- `max_list_items`：每个 `list` 类节点最多展示多少个元素，默认 `1`
- `show_sample`：是否显示基础类型示例值
- `format`：`tree` 或 `markdown`
- `write_to_file`：写入 `.txt`、`.md`、`.markdown` 文件
