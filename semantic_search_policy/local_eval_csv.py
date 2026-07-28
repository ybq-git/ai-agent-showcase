"""对比不同 chain_type 配置对 RAG 回答质量的影响。"""
import csv, os

from policy_qa_agent_v2 import build_qa_chain_from_text

# 加载文档
docs_dir = os.path.join(os.path.dirname(__file__), "docs_txt")
full_text = ""
for fname in sorted(os.listdir(docs_dir)):
    if fname.endswith(".txt"):
        with open(os.path.join(docs_dir, fname), encoding="utf-8") as f:
            full_text += f.read() + "\n\n"

test_cases = [
    ("深圳应届本科生租房补贴标准是多少？", ["1.5万", "15000"]),
    ("深圳人工智能人才奖励最高多少？", ["50万"]),
    ("深圳公积金贷款利率是多少？", ["不知道", "未提及", "无法从给定的信息中找到"]),
]

# 两组配置对比：stuff vs map_reduce（共享向量库，仅 chain_type 不同）
configs = [
    ("stuff", 6),
    ("map_reduce", 6),
]

with open("evaluation_report.csv", "w", newline="", encoding="utf-8") as f:
    writer = csv.writer(f)
    writer.writerow(["配置", "问题", "回答", "是否通过"])

    for chain_type, k in configs:
        label = f"chain={chain_type}, k={k}"
        chain = build_qa_chain_from_text(
            full_text,
            force_rebuild=False,
            chain_type=chain_type,
            k=k,
        )
        for q, keywords in test_cases:
            res = chain.invoke({"query": q})["result"]
            passed = any(kw in res for kw in keywords)
            writer.writerow([label, q, res[:200], "✅" if passed else "❌"])

print("evaluation_report.csv 已生成")
