"""Tool Calling Agent - Streamlit 前端

可视化展示 Agent 的工具调用过程：
  Thought（思考）→ Action（行动）→ Observation（观察）
"""

import sys
import os

sys.path.insert(0, os.path.dirname(__file__))

import streamlit as st
from agent import agent
from langchain_core.messages import HumanMessage, AIMessage, ToolMessage
from langchain_core.callbacks import BaseCallbackHandler


# ========== 回调处理器：捕获 Agent 思考过程 ==========
class AgentCallback(BaseCallbackHandler):
    """捕获 Agent 的工具调用过程"""

    def __init__(self):
        self.steps = []

    def on_tool_start(self, serialized, input_str, **kwargs):
        name = serialized.get("name", "unknown")
        inp = str(input_str)
        if len(inp) > 200:
            inp = inp[:200] + "..."
        self.steps.append(("action", f"🔧 调用工具：**{name}**\n\n> 参数：{inp}"))

    def on_tool_end(self, output, **kwargs):
        out_str = str(output)
        if len(out_str) > 500:
            out_str = out_str[:500] + "...[截断]"
        self.steps.append(("observation", f"📋 工具返回：\n```\n{out_str}\n```"))


st.set_page_config(page_title="Tool Calling Agent", page_icon="🔧", layout="wide")
st.title("🔧 Tool Calling Agent")
st.caption("一个能自主调用工具的 AI 智能体 —— 理解 Function Calling 与 ReAct 模式")

# 侧边栏
with st.sidebar:
    st.header("🛠️ 可用工具")
    st.markdown("""
    | 工具 | 功能 |
    |------|------|
    | 🌤️ `get_weather` | 查询城市天气 |
    | 🧮 `calculator` | 安全数学计算 |
    | 🔍 `web_search` | DuckDuckGo搜索 |
    | 🕐 `get_current_time` | 获取当前时间 |
    """)
    st.divider()
    st.markdown("**💡 试试这些问题：**")
    for tip in [
        "深圳今天天气如何？适合出门吗？",
        "计算 (5689 + 2341) × 17 - 800",
        "搜索最新的 AI Agent 发展趋势",
        "现在几点了？",
        "北京和上海今天哪个更热？",
    ]:
        st.caption(f"- {tip}")
    st.divider()
    st.markdown("**📖 核心概念**")
    st.caption("**Function Calling**：LLM 自主决定何时调用哪个工具")
    st.caption("**ReAct 模式**：Thought → Action → Observation")
    st.caption("**create_agent**：LangGraph 驱动的 Agent 构建器")

# 历史消息
if "messages" not in st.session_state:
    st.session_state.messages = []

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# 用户输入
if prompt := st.chat_input("输入你的问题..."):
    with st.chat_message("user"):
        st.markdown(prompt)
    st.session_state.messages.append({"role": "user", "content": prompt})

    with st.chat_message("assistant"):
        process_expander = st.expander("🔍 查看 Agent 思考过程", expanded=True)
        handler = AgentCallback()

        with st.spinner("Agent 思考中..."):
            try:
                result = agent.invoke(
                    {"messages": [HumanMessage(content=prompt)]},
                    {"callbacks": [handler]},
                )
                # 提取最后一条 AI 消息的文本内容
                messages = result.get("messages", [])
                answer = ""
                for msg in reversed(messages):
                    content = getattr(msg, "content", "")
                    if isinstance(msg, AIMessage) and content:
                        answer = content
                        break
                if not answer:
                    answer = "未能获取回复"
            except Exception as e:
                answer = f"❌ 出错了：{e}"

        with process_expander:
            if handler.steps:
                for _type, content in handler.steps:
                    st.markdown(content)
            else:
                st.caption("（无需调用工具，直接回答）")

        st.markdown(answer)
        st.session_state.messages.append({"role": "assistant", "content": answer})
