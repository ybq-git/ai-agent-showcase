import os, json
from langchain_community.chat_models import ChatTongyi
from langchain_core.messages import HumanMessage
from dotenv import load_dotenv

load_dotenv()
llm = ChatTongyi(model="qwen-max", dashscope_api_key=os.getenv("DASHSCOPE_API_KEY"))

def recommend_resources(weaknesses_json: dict) -> list:
    prompt = f"""
    任务：推荐3个适合应届生的免费学习资源。
    弱点分析：{json.dumps(weaknesses_json, ensure_ascii=False)}
    只输出JSON，不要任何解释、不要markdown代码块、不要前言后语：
    [{{"resource": "资源名", "type": "课程/书籍/项目", "why": "针对什么弱点"}}]
    """
    response = llm.invoke([HumanMessage(content=prompt)])
    content = response.content.strip()
    if content.startswith("```"):
        content = content.split("\n", 1)[-1].rsplit("\n```", 1)[0] if "\n```" in content else content[3:-3]
    # ponytail: find first '[' to last ']', skip any surrounding text
    start, end = content.find("["), content.rfind("]")
    if start != -1 and end > start:
        content = content[start:end+1]
    try:
        return json.loads(content)
    except:
        return [{"resource": "解析失败", "type": "N/A", "why": "N/A"}]


# --- 搜索增强版（原函数保留在上面） ---
from duckduckgo_search import DDGS

def recommend_resources_with_search(weaknesses_json: dict) -> list:
    # 先让模型给出推荐方向
    prompt = f"""
    任务：根据弱点给3个搜索关键词。
    弱点：{json.dumps(weaknesses_json, ensure_ascii=False)}
    只输出JSON，不要任何解释、不要markdown代码块、不要前言后语：
    [{{"keyword": "关键词1"}}, ...]
    """
    res = llm.invoke([HumanMessage(content=prompt)])
    content = res.content.strip()
    if content.startswith("```"):
        content = content.split("\n", 1)[-1].rsplit("\n```", 1)[0] if "\n```" in content else content[3:-3]
    start, end = content.find("["), content.rfind("]")
    if start != -1 and end > start:
        content = content[start:end+1]
    try:
        keywords = json.loads(content)
    except:
        keywords = [{"keyword": "Python"}, {"keyword": "机器学习"}, {"keyword": "项目"}]

    final_recs = []
    try:
        ddgs = DDGS(timeout=10)
        for item in keywords[:3]:
            search_results = ddgs.text(f"{item['keyword']} 免费 教程", max_results=2)
            for sr in search_results:
                final_recs.append({
                    "resource": sr["title"],
                    "link": sr["href"],
                    "type": "搜索推荐",
                    "why": f"针对弱点相关搜索词：{item['keyword']}"
                })
    except Exception:
        # ponytail: 网络不可用时回退到纯模型生成
        return recommend_resources(weaknesses_json)
    return final_recs[:5]
