import jieba
from pathlib import Path
from rank_bm25 import BM25Okapi

from rag.chunking import chunk_text

KNOWLEDGE_DIR = Path(__file__).parent / "knowledge"

_bm25 = None          # 缓存 BM25 索引（建一次就够）
_chunk_texts = []     # 对应的原文块
_meta = []            # 每块来自哪个文档、文档内第几块


def _tokenize(text: str) -> list[str]:
    """把文本切成词列表（中文用 jieba，英文按空白）。"""
    return [w.strip().lower() for w in jieba.cut(text) if w.strip()]


def _build():
    """把所有知识块切词，建 BM25 索引。meta 与向量路格式一致，RRF 才能去重。"""
    global _bm25, _chunk_texts, _meta
    if _bm25 is not None:
        return
    _chunk_texts = []
    _meta = []
    corpus = []
    for path in sorted(KNOWLEDGE_DIR.glob("*.txt")):
        for j, chunk in enumerate(chunk_text(path.read_text(encoding="utf-8"))):
            _chunk_texts.append(chunk)
            _meta.append({"source": path.name, "chunk": j})   # 与 vector 路同格式
            corpus.append(_tokenize(chunk))
    _bm25 = BM25Okapi(corpus)


def bm25_search(query: str, top_k: int = 3) -> list[dict]:
    """BM25 检索：按词频精确匹配，返回统一格式的结果。"""
    _build()
    scores = _bm25.get_scores(_tokenize(query))
    # 按分数从高到低取前 top_k 个
    ranked = sorted(range(len(scores)), key=lambda i: scores[i], reverse=True)[:top_k]
    hits = []
    for i in ranked:
        if scores[i] <= 0:
            continue
        hits.append({
            "text": _chunk_texts[i],
            "source": _meta[i]["source"],
            "chunk": _meta[i]["chunk"],
            "score": float(scores[i]),
        })
    return hits
