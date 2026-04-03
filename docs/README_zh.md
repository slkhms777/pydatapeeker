# PyDataPeekr

PyDataPeekr 是一个用于探查嵌套数据文件和复杂 Python 对象结构的工具，支持清晰的树状输出和 Markdown 输出。它可以帮助你在终端里快速 debug 数据结构和类型，也能帮助 agent 快速查看那些本身不可直接阅读的数据文件内容与结构。

English README: [../README.md](../README.md)
完整 API 文档: [api_zh.md](api_zh.md)

## 1. 支持的文件后缀

`*.pkl` `*.pickle` `*.parquet` `*.json` `*.jsonl` `*.csv` `*.tsv` `*.yaml` `*.yml` `*.npy` `*.npz`

## 2. 安装方式

从 PyPI 安装稳定版：

```bash
pip install pydatapeekr
# 或者
uv pip install pydatapeekr
```

直接从仓库安装最新版（`beta`，可能不稳定）：

```bash
pip install "git+https://github.com/slkhms777/pydatapeekr.git"
# 或者
uv pip install "git+https://github.com/slkhms777/pydatapeekr.git"
```

## 3. CLI 用法

快速开始：

```bash
peek your_file_path
peek --help  # 查看参数
```

## 4. API 用法

```python
import pydatapeekr as peekr

# 获取文件或 Python 对象的渲染结果字符串。
file_text = peekr.inspect_file("data.parquet")
obj_text = peekr.inspect_obj(
    {"user": {"id": 1}, "items": [1, 2, 3]},
    format="markdown",
)

print(file_text)
print(obj_text)

# 直接打印，并带上更适合终端阅读的外壳。
peekr.display_file("data.parquet")  # 默认 style="-"
peekr.display_obj(
    {"user": {"id": 1}, "items": [1, 2, 3]},
    style="#",
)
```

更多 API 示例和完整说明请见 [api_zh.md](api_zh.md)。

## 5. 示例

### Case 1：查看内存中的对象

```python
import pydatapeekr as peekr

# 假设 `raw_image_data` 是一个中间过程里的 DataFrame 变量。
peekr.display_obj(raw_image_data, style="-")
```

终端输出：

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

### Case 2：查看数据文件

```python
import pydatapeekr as peekr

# 示例文件：
# https://huggingface.co/datasets/timm/mini-imagenet/tree/main/data
peekr.display_file("test-00000-of-00002.parquet", style="-")
```

终端输出：

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
