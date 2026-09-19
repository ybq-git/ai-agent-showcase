import os
from pathlib import Path

import chromadb
from openai import OpenAI
from dotenv import load_dotenv

from rag.chunking import chunk_text

load_dotenv()
load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), "..", "..", ".env"))

COLLECTION_NAME = "amazon_rules"
KNOWLEDGE_DIR = Path(__file__).parent / "knowledge"
DB_DIR = Path(__file__).parent / "vector_db"

_client = None
_collection = None


class DashScopeEmbedding:
    """自定义 embedding 函数：调通义 text-embedding-v3（一次最多 10 条，分批调）。"""

    @staticmethod
    def name() -> str:
        """chroma 要求每个 embedding 函数报名字，用来判断是否默认。"""
        return "dashscope-text-embedding-v3"

    def __init__(self):
        self._client = OpenAI(
            api_key=os.getenv("DASHSCOPE_API_KEY"),
            base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
        )

    def __call__(self, input):
        """批量入库时 chroma 会调它：输入文本列表，返回向量列表。"""
        all_vectors = []
        batch = []
        for text in input:
            batch.append(text)
            if len(batch) >= 10:          # 攒满 10 条就调一次
                resp = self._client.embeddings.create(model="text-embedding-v3", input=batch)
                all_vectors.extend(item.embedding for item in resp.data)
                batch = []                # 清空，装下一批
        if batch:                          # 最后剩的不满 10 条的也要调
            resp = self._client.embeddings.create(model="text-embedding-v3", input=batch)
            all_vectors.extend(item.embedding for item in resp.data)
        return all_vectors

    def embed_query(self, input) -> list[list[float]]:
        #"""chroma 查询时会调它(input 已是文本列表）。要返回"向量的列表"。"""
        resp = self._client.embeddings.create(model="text-embedding-v3", input=input)
        return [resp.data[0].embedding]


def _get_collection():
    """懒初始化：第一次调用时建库，之后复用（避免重复初始化）。"""
    global _client, _collection
    if _collection is None:
        _client = chromadb.PersistentClient(path=str(DB_DIR))
        emb = DashScopeEmbedding()
        _collection = _client.get_or_create_collection(
            name=COLLECTION_NAME, embedding_function=emb
        )
    return _collection


def build_index():
    """把 knowledge/ 里的所有文档分块后写入向量库（先清空再写）。"""
    collection = _get_collection()

    # 清空
    existing = collection.get()["ids"]
    if existing:
        collection.delete(ids=existing)

    docs, metas, ids = [], [], []
    for i, path in enumerate(sorted(KNOWLEDGE_DIR.glob("*.txt"))):
        text = path.read_text(encoding="utf-8")
        for j, chunk in enumerate(chunk_text(text)):
            docs.append(chunk)
            metas.append({"source": path.name, "chunk": j})
            ids.append(f"doc{i}_chunk{j}")

    if docs:
        collection.add(documents=docs, metadatas=metas, ids=ids)
    return len(docs)


def vector_search(query: str, top_k: int = 3) -> list[dict]:
    """语义检索：把问题也 embedding，找最相似的块。"""
    collection = _get_collection()
    result = collection.query(query_texts=[query], n_results=top_k)
    # 转成统一格式 [{text, source, chunk, score}]，方便后面 RRF 融合
    hits = []
    for j, doc in enumerate(result["documents"][0]):
        meta = result["metadatas"][0][j]
        hits.append({
            "text": doc,
            "source": meta.get("source", ""),
            "chunk": meta.get("chunk", 0),
            "score": 1.0 - (result["distances"][0][j] if result["distances"] else 0),
        })
    return hits
