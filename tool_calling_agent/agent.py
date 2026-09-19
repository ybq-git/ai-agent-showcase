"""Tool Calling Agent - 支持天气查询、计算器、网页搜索、日期时间等工具的智能体

核心学习点：Function Calling（工具调用）、ReAct 决策循环、多工具编排

LangChain 1.3+ 新 API：使用 create_agent 和 StateGraph 构建 Agent
"""

import os
import sys
from dotenv import load_dotenv

# 加载 .env（先加载当前目录，再加载上级目录的公共 .env）
load_dotenv()
load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), "..", ".env"))

from langchain_community.chat_models import ChatTongyi
from langchain.agents import create_agent

from tools.weather import get_weather
from tools.calculator import calculator
from tools.search import web_search
from tools.datetime_utils import get_current_time


# ========== 1. LLM 实例 ==========
def get_llm():
    api_key = os.getenv("DASHSCOPE_API_KEY")
    if not api_key:
        raise RuntimeError("未配置 DASHSCOPE_API_KEY，请在 .env 中设置")
    return ChatTongyi(model="qwen-max", dashscope_api_key=api_key)


# ========== 2. 工具集 ==========
tools = [get_weather, calculator, web_search, get_current_time]

# ========== 3. 系统 Prompt ==========
system_prompt = """你是一个智能助手，可以调用工具来回答用户的问题。

使用工具时遵循以下规则：
1. 当用户问天气时，调用 get_weather 工具
2. 当用户需要计算时，调用 calculator 工具
3. 当用户需要搜索最新信息时，调用 web_search 工具
4. 当用户问当前时间时，调用 get_current_time 工具
5. 如果不需要工具就直接回答

重要：给用户的回复必须用中文。"""


# ========== 4. 构建 Agent（LangChain 1.3+ 新 API） ==========
agent = create_agent(
    model=get_llm(),
    tools=tools,
    system_prompt=system_prompt,
)


# ========== 5. 运行入口 ==========
def run(query: str) -> str:
    """执行 Agent 并返回最终回复"""
    result = agent.invoke(
        {"messages": [{"role": "user", "content": query}]}
    )
    # 取最后一条 AI 消息
    messages = result.get("messages", [])
    for msg in reversed(messages):
        if hasattr(msg, "content") and msg.type == "ai":
            return msg.content
    return "未能获取回复"


if __name__ == "__main__":
    # 快速自测：3 个覆盖不同 Tool 的场景
    test_queries = [
        "北京今天天气怎么样？",
        "帮我算一下 (123 + 456) * 78 - 1000 等于多少",
        "现在是几点？",
    ]
    for q in test_queries:
        print(f"\n{'='*60}")
        print(f"用户：{q}")
        print(f"Agent：{run(q)}")
