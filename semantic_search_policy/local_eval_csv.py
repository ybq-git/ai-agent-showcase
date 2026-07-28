import csv, os

from policy_qa_agent_v2 import build_qa_chain_from_text

# 加载政策文档构建问答链
docs_dir = os.path.join(os.path.dirname(__file__), "docs_txt")
full_text = ""
for fname in os.listdir(docs_dir):
    if fname.endswith(".txt"):
        with open(os.path.join(docs_dir, fname), encoding="utf-8") as f:
            full_text += f.read() + "\n\n"

chain = build_qa_chain_from_text(full_text)
test_cases = [
    ("应届生租房补贴标准", ["1.5万","15000"]),
    ("人工智能人才奖励", ["50万"]),
    ("公积金贷款利率", ["不知道","未提及"])
]

with open("evaluation_report.csv", "w", newline='', encoding="utf-8") as f:
    writer = csv.writer(f)
    writer.writerow(["问题", "回答", "是否通过"])
    for q, keywords in test_cases:
        res = chain.invoke({"query": q})["result"]
        passed = any(kw in res for kw in keywords)
        writer.writerow([q, res[:100], "是" if passed else "否"])
print("evaluation_report.csv 已生成")
