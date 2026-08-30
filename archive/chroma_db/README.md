# ChromaDB 基础操作演示

用 **ChromaDB + sentence-transformers 中文模型** 演示向量库的基本操作：建集合 → 加文档 → 相似查询 → 更新 → 删除。

- 用免费模型 `paraphrase-multilingual-MiniLM-L12-v2`，数据持久化到本地 `chroma_db/` 目录。
- 设置了 `HF_ENDPOINT=https://hf-mirror.com`（国内用镜像站下载模型）。

**为什么在 archive**：这是"认识向量库"的单文件练习，也是后面 RAG 作品（`semantic_search_policy`）的前置练手。正式 RAG 项目已单列在作品集里。

## 怎么跑

1. `pip install chromadb sentence-transformers`
2. `python chroma_demo.py`

## 文件

- `chroma_demo.py` —— 建集合/加文档/查询/更新/删除 的完整演示
