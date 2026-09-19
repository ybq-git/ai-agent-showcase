def rrf_fuse(vector_hits:list[dict],bm25_hits:list[dict],k:int = 60) ->list[dict]:
    """把向量和 BM25 两路结果按 RRF 融合排序。

    只看每路的排名(第1名贡献1/(k+1), 第2名1/(k+2)...),
    同一文档在两路的贡献相加 = 融合分, 越高越靠前。
    """
    # 1) 先把两路结果按"内容"合并:同一块文档可能两路都命中
    #    用 (source, chunk) 当唯一键
    merged ={}         # key -> {"text":..., "source":..., "chunk":..., "rrf_score": 累计分}
    #向量路：第1名贡献 1/（k+1），第2名 1/（k+2）
    for rank, hit in enumerate(vector_hits, start=1):
        key = (hit["source"], hit["chunk"])
        if key not in merged:
            merged[key] = {"text": hit["text"], "source": hit["source"],
                           "chunk": hit["chunk"], "rrf_score": 0.0}
        merged[key]["rrf_score"] += 1.0 / (k + rank)

    # BM25 路:同样累加
    for rank, hit in enumerate(bm25_hits, start=1):
        key = (hit["source"], hit["chunk"])
        if key not in merged:
            merged[key] = {"text": hit["text"], "source": hit["source"],
                           "chunk": hit["chunk"], "rrf_score": 0.0}
        merged[key]["rrf_score"] += 1.0 / (k + rank)

    # 2) 按融合分从高到低排序
    results = sorted(merged.values(), key=lambda h: h["rrf_score"], reverse=True)
    return results