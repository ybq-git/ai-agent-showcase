"""引用覆盖率评估：答案是否带上了该引用的证据。

注意：这里只做评测。真正的回答链路在 rag/answer.py。
"""
import os, sys
sys.stdout.reconfigure(encoding='utf-8')

from rag.hybrid import hybrid_search
from rag.answer import answer_with_citations

# (问题, 应引用的来源)
QA = [
    ("标题最多不能超过多少字符?", "亚马逊商品标题规范.txt"),
    ("卖没授权的品牌货会怎样?", "亚马逊禁售与合规.txt"),
]


def eval_citation_coverage() -> float:
    covered = 0
    for question, expected_source in QA:
        ctx = hybrid_search(question, top_k=3)["context"]
        result = answer_with_citations(question, ctx)
        # 引用了第几段?
        cited_idx = result.get("citations", [])
        cited_sources = {ctx[i-1]["source"] for i in cited_idx if 1 <= i <= len(ctx)}
        ok = expected_source in cited_sources
        covered += 1 if ok else 0
        print(f"  Q: {question} → 引用 {cited_sources} 期望 {expected_source} {'✅' if ok else '❌'}")
    return covered / len(QA)
