"""带引用标注的政策问答：Hybrid 检索 → LLM 只依据资料作答 → 标注用了哪几段。

这是回答链路本身；质量评测（引用覆盖率）在 rag/eval_quality.py。
"""
from rag.hybrid import hybrid_search
from ai.factory import get_llm_provider
from ai.base import LLMMessage
from ai.parse import parse_llm_json

SYSTEM_PROMPT = (
    "你是政策问答助手。只能依据给定资料回答,并在句尾用 [n] 标注用了哪段资料。"
    "只输出 JSON: {\"answer\": ..., \"citations\": [n, ...]}"
)


def answer_with_citations(question: str, context: list[dict]) -> dict:
    """把检索到的上下文喂给 LLM，要求回答时标注 [来源]。"""
    llm = get_llm_provider()
    ctx_text = "\n\n".join(f"[{i+1}] {c['text']}" for i, c in enumerate(context))
    messages = [
        LLMMessage(role="system", content=SYSTEM_PROMPT),
        LLMMessage(role="user", content=f"问题:{question}\n\n资料:\n{ctx_text}"),
    ]
    raw = llm.complete(messages)
    return parse_llm_json(raw.content)


def ask(question: str, top_k: int = 5) -> dict:
    """检索 → 作答，返回答案与它实际引用了哪几个来源。"""
    context = hybrid_search(question, top_k=top_k)["context"]
    if not context:
        return {"answer": "资料库里没有找到相关内容，无法回答。", "citations": [], "sources": [], "context": []}

    result = answer_with_citations(question, context)
    cited = result.get("citations") or []
    return {
        "answer": result.get("answer", ""),
        "citations": cited,
        "sources": [context[i - 1]["source"] for i in cited if 1 <= i <= len(context)],
        "context": [{"source": c["source"], "chunk": c.get("chunk"), "text": c["text"]} for c in context],
    }
