"""网页搜索工具

使用 DuckDuckGo 搜索引擎进行网页搜索
"""

from langchain_community.tools import DuckDuckGoSearchRun
from langchain_core.tools import tool


# 使用 langchain_community 封装的 DuckDuckGo 搜索
_ddg_search = DuckDuckGoSearchRun()


@tool
def web_search(query: str) -> str:
    """在互联网上搜索最新信息。参数 query 为搜索关键词。

    返回搜索结果摘要。当用户询问时事、新闻、最新动态等信息时使用。
    """
    try:
        result = _ddg_search.invoke(query)
        # 截断过长的结果
        if len(result) > 2000:
            result = result[:2000] + "\n...[结果过长，已截断]"
        return result
    except Exception as e:
        return f"搜索出错：{e}。请稍后重试或尝试更换关键词。"
