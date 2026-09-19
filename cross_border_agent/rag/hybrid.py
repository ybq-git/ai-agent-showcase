from rag.vector import vector_search
from rag.bm25 import bm25_search
from rag.rrf import rrf_fuse

UNTRUSTED_MARKERS = ["untrusted_", "user_uploaded_"]   # 文件名带这些 = 不可信


def is_trusted(source: str) -> bool:
    """信任过滤:文件名带不可信标记的,拒绝。fail-closed:默认可信度存疑就拦。"""
    return not any(marker in source for marker in UNTRUSTED_MARKERS)


def hybrid_search(query: str, top_k: int = 5, max_chars: int = 1500) -> dict:
    """完整检索:向量+BM25 → RRF 融合 → 信任过滤 → 打包。"""
    vector_hits = vector_search(query, top_k=top_k)
    bm25_hits = bm25_search(query, top_k=top_k)
    fused = rrf_fuse(vector_hits, bm25_hits)

    # ① 信任过滤:只留可信来源
    trusted = [h for h in fused if is_trusted(h["source"])]

    # ③ 预算打包:按顺序塞,超字符上限就停
    context_chunks = []
    total = 0
    for h in trusted:
        if total + len(h["text"]) > max_chars:
            break
        context_chunks.append(h)
        total += len(h["text"])

    return {"context": context_chunks, "total_chars": total}
