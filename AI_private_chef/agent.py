# -*- coding: utf-8 -*-
"""
私人厨师智能食谱推荐系统 —— 后端核心模块
负责：环境初始化、LLM/Agent 创建、消息构造、对话调用
"""

import base64
import os
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

from dotenv import load_dotenv
from langchain.agents import create_agent
from langchain_core.messages import HumanMessage
from langchain_openai import ChatOpenAI
from langchain_tavily import TavilySearch
from langgraph.checkpoint.sqlite import SqliteSaver

# ── 模块级根目录 ────────────────────────────────────────────
_PROJECT_DIR = Path(__file__).parent
_RESOURCES_DIR = _PROJECT_DIR / "resources"
_DB_PATH = _RESOURCES_DIR / "personal_chef.db"

# ── 模块级单例（初始化一次） ───────────────────────────────
_agent = None


def _ensure_resources_dir() -> None:
    """创建 resources 目录（如不存在）"""
    _RESOURCES_DIR.mkdir(exist_ok=True)
    _ensure_db_schema()


def _ensure_db_schema() -> None:
    """确保数据库表有 sessions 表存储会话创建时间"""
    conn = sqlite3.connect(str(_DB_PATH))
    try:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS sessions (
                thread_id TEXT PRIMARY KEY,
                created_at INTEGER NOT NULL
            )
        """)
        conn.commit()
    except:
        pass
    finally:
        conn.close()


def get_agent():
    """
    返回已初始化的 Agent（单例）。
    Streamlit 中可用 @st.cache_resource 包裹此函数以避免重复初始化。
    """
    global _agent
    if _agent is not None:
        return _agent

    # 优先当前目录的 .env，其次父目录（项目根）
    env_path = _PROJECT_DIR / ".env"
    if not env_path.exists():
        env_path = _PROJECT_DIR.parent / ".env"
    load_dotenv(env_path)

    llm = ChatOpenAI(
        model="qwen3.5-plus",
        openai_api_base=os.getenv("DASHSCOPE_BASE_URL"),
        openai_api_key=os.getenv("DASHSCOPE_API_KEY"),
    )

    web_search = TavilySearch(
        max_results=5,
        topic="general",
        tavily_api_key=os.getenv("TAVILY_API_KEY"),
    )

    _ensure_resources_dir()
    connection = sqlite3.connect(str(_DB_PATH), check_same_thread=False)
    checkpoint = SqliteSaver(connection)
    checkpoint.setup()

    system_prompt = """
您是一名专业的私人厨师。收到用户提供的食材照片或清单后，请严格按照以下流程操作：

1. 识别和评估食材：若用户提供照片，首先辨识所有可见食材。基于食材的外观状态，评估其新鲜度与可用量，整理出一份"当前可用食材清单"。

2. 智能食谱检索：优先调用 web_search 工具，以"可用食材清单"为核心关键词，查找可行菜谱。

3. 多维度评估与排序：从营养价值和制作难度两个维度对检索到的候选食谱进行量化打分，并根据得分排序，制作简单且营养丰富的排名菜单。

4. 结构化方案输出：把排序后的食谱整理为一份结构清晰的建议报告，要包含食谱信息、得分、推荐理由、食谱的参考图片，帮助用户快速做出决策。

请严格按照流程执行，优先调用 web_search 工具搜索食谱，搜索不到的情况下才能自己发挥。
"""

    _agent = create_agent(
        model=llm,
        system_prompt=system_prompt,
        tools=[web_search],
        checkpointer=checkpoint,
    )
    return _agent


def build_message(text: str, image_source: str | bytes | None = None) -> HumanMessage:
    """
    构造多模态消息。
    image_source: 图片 URL（str）或图片 bytes（本地上传），为 None 时纯文本。
    """
    content: list = [{"type": "text", "text": text}]

    if image_source is not None:
        if isinstance(image_source, bytes):
            b64 = base64.b64encode(image_source).decode("utf-8")
            image_url = f"data:image/jpeg;base64,{b64}"
        else:
            image_url = image_source
        content.append({"type": "image_url", "image_url": {"url": image_url}})

    return HumanMessage(content)


def _save_session_time(thread_id: str) -> None:
    """保存会话创建时间（首次调用时）"""
    conn = sqlite3.connect(str(_DB_PATH))
    try:
        conn.execute(
            "INSERT OR IGNORE INTO sessions (thread_id, created_at) VALUES (?, ?)",
            (thread_id, int(datetime.now().timestamp()))
        )
        conn.commit()
    except:
        pass
    finally:
        conn.close()


def chat(
    text: str,
    image_source: str | bytes | None = None,
    thread_id: str = "default",
) -> list:
    """
    执行一次对话。
    返回 LangGraph 响应中的所有消息列表。
    """
    _save_session_time(thread_id)
    agent = get_agent()
    message = build_message(text, image_source)
    config = {"configurable": {"thread_id": thread_id}}
    response = agent.invoke({"messages": [message]}, config)
    return response["messages"]


def list_sessions() -> list[dict]:
    """返回所有历史会话列表，按创建时间倒序（最新在前），含时间标签"""
    _ensure_resources_dir()
    conn = sqlite3.connect(str(_DB_PATH))
    try:
        rows = conn.execute(
            """SELECT c.thread_id, COUNT(*) as cnt, s.created_at
               FROM checkpoints c
               LEFT JOIN sessions s ON c.thread_id = s.thread_id
               GROUP BY c.thread_id
               ORDER BY COALESCE(s.created_at, 0) DESC"""
        ).fetchall()
        result = []
        for r in rows:
            thread_id = r[0]
            created_at = r[2]
            time_label = ""
            try:
                if created_at:
                    dt = datetime.fromtimestamp(created_at, tz=timezone.utc)
                    local_dt = dt.astimezone()
                    time_label = (
                        f"{local_dt.year}.{local_dt.month}.{local_dt.day}_"
                        f"{local_dt.hour:02d}-{local_dt.minute:02d}-{local_dt.second:02d}"
                    )
                else:
                    if _DB_PATH.exists():
                        mtime = _DB_PATH.stat().st_mtime
                        dt = datetime.fromtimestamp(mtime, tz=timezone.utc)
                        local_dt = dt.astimezone()
                        time_label = (
                            f"{local_dt.year}.{local_dt.month}.{local_dt.day}_"
                            f"{local_dt.hour:02d}-{local_dt.minute:02d}-{local_dt.second:02d}"
                        )
            except (ValueError, OSError):
                time_label = ""
            result.append({
                "thread_id": thread_id,
                "message_count": r[1],
                "time_label": time_label,
            })
        return result
    finally:
        conn.close()


def load_history(thread_id: str) -> list[dict]:
    """
    从 LangGraph checkpoint 恢复历史消息。
    返回 [{role: 'user'|'assistant', content: '...'}, ...]
    """
    agent = get_agent()
    config = {"configurable": {"thread_id": thread_id}}
    try:
        state = agent.get_state(config)
    except Exception:
        return []
    if state is None or not hasattr(state, "values"):
        return []
    msgs = state.values.get("messages", [])
    result = []
    for m in msgs:
        role = getattr(m, "type", None)
        content = getattr(m, "content", "")
        if role == "human":
            # 用户消息只显示输入的问题文本，忽略图片等多模态内容
            if isinstance(content, list):
                text_parts = [
                    c.get("text", "")
                    for c in content
                    if isinstance(c, dict) and c.get("type") == "text"
                ]
                text = "\n".join(p for p in text_parts if p)
            else:
                text = str(content) if content else ""
            if text:
                result.append({"role": "user", "content": text})
        elif role == "ai" and content:
            result.append({"role": "assistant", "content": content})
    return result


def delete_session(thread_id: str) -> None:
    """删除指定会话及其所有检查点数据"""
    _ensure_resources_dir()
    conn = sqlite3.connect(str(_DB_PATH))
    try:
        conn.execute("DELETE FROM checkpoints WHERE thread_id = ?", (thread_id,))
        conn.execute("DELETE FROM writes WHERE thread_id = ?", (thread_id,))
        conn.execute("DELETE FROM sessions WHERE thread_id = ?", (thread_id,))
        conn.commit()
    finally:
        conn.close()
