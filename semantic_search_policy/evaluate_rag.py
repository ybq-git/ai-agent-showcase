"""
读取测试问题，逐条询问RAG Agent，记录答案并人工打分。
"""
import json, os
from policy_qa_agent_v2 import qa_chain  # 直接复用昨天的链

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
with open(os.path.join(BASE_DIR, "test_questions.txt"), "r", encoding="utf-8") as f:
    questions = [line.strip() for line in f if line.strip()]

results = []
for i, q in enumerate(questions, 1):
    print(f"处理第{i}/{len(questions)}问：{q}")
    answer = qa_chain({"query": q})
    results.append({
        "question": q,
        "answer": answer["result"],
        "sources": [doc.metadata["source"] for doc in answer["source_documents"]]
    })
    # 简单显示
    print("回答：", answer["result"][:100])
    print("---")

# 保存评测记录
with open(os.path.join(BASE_DIR, "evaluation_raw.json"), "w", encoding="utf-8") as out:
    json.dump(results, out, ensure_ascii=False, indent=2)
print("评测结果已保存到 evaluation_raw.json")
