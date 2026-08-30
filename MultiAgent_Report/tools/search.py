import re

import requests
from langchain_core.tools import tool

MAX_RESULTS = 5


def _search(query: str) -> list[dict]:
    """Bing 搜索（DuckDuckGo 等在国内网络不可达，Bing 可用）。"""
    resp = requests.get(
        "https://cn.bing.com/search",
        params={"q": query, "mkt": "zh-CN", "setlang": "zh-hans", "cc": "CN", "ensearch": 0},
        headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36"},
        timeout=10,
    )
    resp.raise_for_status()
    results = []
    for item in re.findall(r'<li class="b_algo".*?</li>', resp.text, re.S):
        h2 = re.search(r"<h2[^>]*>(.*?)</h2>", item, re.S)
        if not h2:
            continue
        a = re.search(r'href="([^"]+)"', h2.group(1))
        if not a:
            continue
        title = re.sub(r"<[^>]+>", "", h2.group(1))
        body = re.search(r"<p[^>]*>(.*?)</p>", item, re.S)
        results.append(
            {
                "title": title,
                "href": a.group(1),
                "body": re.sub(r"<[^>]+>", "", body.group(1)) if body else "",
            }
        )
    return results[:MAX_RESULTS]


def _format(results: list[dict]) -> str:
    lines = [
        f"## {r.get('title', '')}\n{r.get('href', '')}\n{r.get('body', '')}"
        for r in results
    ]
    return "\n\n".join(lines) or "无搜索结果"


@tool
def web_search(query: str) -> str:
    """搜索网络并返回结果文本，用于获取实时信息。"""
    try:
        return _format(_search(query))
    except Exception as e:
        return f"网络搜索错误: {str(e)}"


if __name__ == "__main__":
    assert _format([{"title": "python", "href": "https://x", "body": "body"}]) == "## python\nhttps://x\nbody"
    assert _format([]) == "无搜索结果"
    print("self-check ok")
