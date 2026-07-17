from duckduckgo_search import DDGS

# ponytail: 国内网络 DuckDuckGo 超时，fallback 到模型直接生成
# 见 resource_recommender_agent.py — 已用通义千问直接推荐资源
try:
    ddgs = DDGS(timeout=10)
    results = ddgs.text("2026 AI Agent开发 学习资源 免费课程", max_results=3)
    for r in results:
        print(r["title"], r["href"])
except Exception as e:
    print(f"搜索失败（网络限制）: {e}")
    print("已跳过 — resource_recommender_agent.py 使用模型直接生成资源推荐")
