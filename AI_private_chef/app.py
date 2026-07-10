# -*- coding: utf-8 -*-
"""
私人厨师智能食谱推荐系统 —— Streamlit 前端
启动方式：streamlit run app.py
"""

import uuid
from datetime import datetime

import streamlit as st
import streamlit.components.v1 as components

from agent import chat, delete_session, get_agent, list_sessions, load_history


def _now_label() -> str:
    """生成对话时间标签，格式：2026.7.10_18-23-34（月/日不补零）"""
    now = datetime.now()
    return (
        f"{now.year}.{now.month}.{now.day}_"
        f"{now.hour:02d}-{now.minute:02d}-{now.second:02d}"
    )

# ── 页面配置 ──────────────────────────────────────────────────
st.set_page_config(
    page_title="私人厨师 | AI 食谱推荐",
    page_icon="🍳",
    layout="wide",
)

# ── 自定义 CSS：暖调厨房主题 ─────────────────────────────────
st.markdown("""
<style>
    .stApp {
        background: linear-gradient(170deg, #FFF9F2 0%, #FFF3E6 30%, #FDF0E0 60%, #FEFAF5 100%);
    }

    /* 聊天区水印 */
    section[data-testid="stChatMessageContainer"] > div {
        background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='600' height='600' viewBox='0 0 600 600'%3E%3Cg fill='%23D4B896' opacity='0.07'%3E%3Cpath d='M120 100 L128 90 L132 90 L140 100 L138 130 L122 130 Z'/%3E%3Crect x='250' y='80' width='8' height='50' rx='4'/%3E%3Cpath d='M246 80 Q254 60 262 80'/%3E%3Cellipse cx='420' cy='110' rx='14' ry='20'/%3E%3Crect x='416' y='130' width='8' height='40' rx='3'/%3E%3Crect x='80' y='240' width='80' height='60' rx='8'/%3E%3Crect x='70' y='230' width='100' height='14' rx='6'/%3E%3Ccircle cx='100' cy='270' r='18' fill='none' stroke='%23D4B896' stroke-width='5'/%3E%3Ccircle cx='350' cy='280' r='50' fill='none' stroke='%23D4B896' stroke-width='4'/%3E%3Ccircle cx='350' cy='280' r='25' fill='none' stroke='%23D4B896' stroke-width='3'/%3E%3Cline x1='520' y1='220' x2='520' y2='260' stroke='%23D4B896' stroke-width='4'/%3E%3Cellipse cx='520' cy='210' rx='6' ry='12' fill='none' stroke='%23D4B896' stroke-width='3'/%3E%3Crect x='180' y='430' width='70' height='12' rx='6'/%3E%3Crect x='420' y='400' width='20' height='30' rx='4'/%3E%3Crect x='424' y='394' width='12' height='10' rx='4'/%3E%3C/g%3E%3C/svg%3E");
        background-repeat: repeat;
        background-size: 450px 450px;
        background-position: center;
        background-attachment: fixed;
        border-radius: 20px;
    }

    /* 标题 */
    .main-title {
        text-align: center; font-size: 2.4rem; font-weight: 800;
        background: linear-gradient(135deg, #D2691E 0%, #E8742A 40%, #C0392B 100%);
        -webkit-background-clip: text; -webkit-text-fill-color: transparent;
        background-clip: text; margin-bottom: 0; letter-spacing: 2px;
    }
    .main-subtitle { text-align: center; color: #B0937A; font-size: 0.95rem; margin-bottom: 0.8rem; }

    /* 侧边栏 */
    [data-testid="stSidebar"] { background: linear-gradient(180deg, #1E1008 0%, #2C1810 40%, #3E2216 100%); }
    [data-testid="stSidebar"] * { color: #E8D5C4 !important; }
    [data-testid="stSidebar"] h1, [data-testid="stSidebar"] h2, [data-testid="stSidebar"] h3 { color: #F5A623 !important; }
    [data-testid="stSidebar"] hr { border-color: rgba(255,255,255,0.10); }
    [data-testid="stSidebar"] button {
        border: 1px solid rgba(255,255,255,0.12) !important;
        background: rgba(255,255,255,0.05) !important;
        color: #E8D5C4 !important; border-radius: 10px !important; transition: all 0.2s;
    }
    [data-testid="stSidebar"] button:hover { background: rgba(245,166,35,0.15) !important; border-color: #F5A623 !important; }

    /* 聊天气泡 */
    [data-testid="stChatMessage"] {
        background: rgba(255,255,255,0.88) !important; backdrop-filter: blur(10px);
        border-radius: 18px !important; border: 1px solid rgba(210,180,140,0.25);
        box-shadow: 0 2px 12px rgba(0,0,0,0.04); margin-bottom: 0.5rem;
    }
    [data-testid="stChatMessage"] * { color: #1A1A1A !important; }

    /* 隐藏杂项 */
    footer { visibility: hidden; } #MainMenu { visibility: hidden; }
    header[data-testid="stHeader"] { background: transparent; }
    ::-webkit-scrollbar { width: 6px; }
    ::-webkit-scrollbar-track { background: transparent; }
    ::-webkit-scrollbar-thumb { background: #D4B896; border-radius: 3px; }
    ::-webkit-scrollbar-thumb:hover { background: #B8937A; }

    /* === 输入框左侧的「+」添加图片按钮 === */
    div[data-testid="stPopover"] > button {
        width: 42px !important;
        height: 42px !important;
        min-height: 42px !important;
        max-height: 42px !important;
        border-radius: 10px !important;
        background: linear-gradient(135deg, #F5A623 0%, #D2691E 100%) !important;
        color: #fff !important;
        border: 2px solid rgba(255,255,255,0.7) !important;
        box-shadow: 0 2px 8px rgba(210,105,30,0.35) !important;
        font-size: 1.4rem !important;
        font-weight: 800 !important;
        line-height: 1 !important;
        padding: 0 !important;
        margin: 0 !important;
        position: relative !important;
        display: flex !important;
        align-items: center !important;
        justify-content: center !important;
        transition: transform 0.15s, box-shadow 0.15s !important;
    }
    div[data-testid="stPopover"] > button:hover {
        transform: scale(1.04) !important;
        box-shadow: 0 4px 14px rgba(210,105,30,0.5) !important;
        background: linear-gradient(135deg, #F5A623 0%, #D2691E 100%) !important;
        border-color: #fff !important;
        color: #fff !important;
    }
    div[data-testid="stPopover"] > button svg { display: none !important; }
    div[data-testid="stPopover"] > button p {
        font-size: 1.4rem !important;
        font-weight: 800 !important;
        line-height: 1 !important;
        color: #fff !important;
        margin: 0 !important;
        padding: 0 !important;
    }

    /* ── 为固定输入栏留出底部空间 ── */
    .chat-messages-area {
        padding-bottom: 90px !important;
    }

    /* ── 底部固定输入栏（深色主题） ── */
    .fixed-input-bar {
        position: fixed !important;
        bottom: 15px !important;
        left: calc(21rem + 15px) !important;
        width: calc(100% - 21rem - 30px) !important;
        background: #1a1a1a !important;
        padding: 10px 15px 15px !important;
        border: 1px solid #333 !important;
        border-radius: 12px !important;
        z-index: 100 !important;
        display: flex !important;
        align-items: center !important;
        gap: 8px !important;
        box-sizing: border-box !important;
    }

    /* ── 输入框样式（深色主题） ── */
    .fixed-input-bar [data-testid="stTextInput"] {
        flex: 1 !important;
    }
    .fixed-input-bar [data-testid="stTextInput"] input {
        background: #2a2a2a !important;
        border: 1px solid #444 !important;
        border-radius: 8px !important;
        color: #fff !important;
        caret-color: #F5A623 !important;
        padding: 10px 15px !important;
        font-size: 14px !important;
    }
    .fixed-input-bar [data-testid="stTextInput"] input:focus {
        border-color: #F5A623 !important;
        box-shadow: 0 0 0 2px rgba(245,166,35,0.3) !important;
        outline: none !important;
    }
    .fixed-input-bar [data-testid="stTextInput"] input::placeholder {
        color: #666 !important;
    }

    /* ── 发送按钮样式（深色主题） ── */
    .fixed-input-bar [data-testid="stButton"] button {
        background: #F5A623 !important;
        color: #fff !important;
        border: none !important;
        border-radius: 8px !important;
        padding: 10px 20px !important;
        font-weight: 600 !important;
    }
    .fixed-input-bar [data-testid="stButton"] button:hover {
        background: #D2691E !important;
    }

    /* popover 展开面板样式 */
    div[data-testid="stPopover"] [data-state="open"] {
        border-radius: 12px !important;
        box-shadow: 0 6px 24px rgba(0,0,0,0.15) !important;
        border: 1px solid rgba(210,180,140,0.25) !important;
        padding: 6px 4px !important;
    }
</style>
""", unsafe_allow_html=True)

# ── 标题 ──────────────────────────────────────────────────────
st.markdown('<p class="main-title">🍳 私人厨师</p>', unsafe_allow_html=True)
st.markdown('<p class="main-subtitle">AI 智能食谱推荐 · 上传食材，秒出菜单</p>', unsafe_allow_html=True)

# ── 初始化 Agent ──────────────────────────────────────────────
get_agent_cached = st.cache_resource(get_agent)
get_agent_cached()

# ── session_state ─────────────────────────────────────────────
if "thread_id" not in st.session_state:
    st.session_state.thread_id = str(uuid.uuid4())
if "created_at" not in st.session_state:
    st.session_state.created_at = _now_label()
if "messages" not in st.session_state:
    st.session_state.messages = []
if "delete_target" not in st.session_state:
    st.session_state.delete_target = None
if "pending_image" not in st.session_state:
    st.session_state.pending_image = None
if "img_menu_mode" not in st.session_state:
    st.session_state.img_menu_mode = None
if "input_counter" not in st.session_state:
    st.session_state.input_counter = 0

# ── 侧边栏 ────────────────────────────────────────────────────
with st.sidebar:
    # Logo
    st.markdown("""
    <div style="text-align:center; padding:0.3rem 0 1rem 0;">
        <span style="font-size:2.6rem;">👨‍🍳</span>
        <p style="font-weight:700; font-size:1.05rem; margin:0; letter-spacing:1px;">私人厨师</p>
    </div>
    """, unsafe_allow_html=True)

    st.divider()

    # ── 新对话 + 导出 ──
    b1, b2 = st.columns(2)
    with b1:
        if st.button("✨ 新对话", use_container_width=True):
            st.session_state.thread_id = str(uuid.uuid4())
            st.session_state.created_at = _now_label()
            st.session_state.messages = []
            st.session_state.pending_image = None
            st.session_state.img_menu_mode = None
            st.session_state.input_counter += 1
            st.rerun()
    with b2:
        export_text = "\n\n".join(
            f"**{'🧑 你' if m['role']=='user' else '👨‍🍳 厨师'}**\n{m['content']}"
            for m in st.session_state.messages
        )
        st.download_button("📥 导出", data=export_text or "(空)",
            file_name=f"chat_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md",
            mime="text/markdown", use_container_width=True,
            disabled=len(st.session_state.messages) == 0)

    st.divider()

    # ── 历史会话（按时间倒序） ──
    st.markdown("#### 📜 历史会话")
    sessions = list_sessions()
    if not sessions:
        st.caption("暂无历史会话")

    for s in sessions:
        tid = s["thread_id"]
        is_current = tid == st.session_state.thread_id
        time_label = s.get("time_label", "")

        label = f"{'🟠 ' if is_current else '📝 '}{time_label}  ·  {s['message_count']} 轮" if time_label else f"{'🟠 ' if is_current else '📝 '}{tid[:8]}...  ·  {s['message_count']} 轮"

        col1, col2 = st.columns([4, 1])
        with col1:
            if not is_current:
                if st.button(label, key=f"session_{tid}", use_container_width=True):
                    history = load_history(tid)
                    st.session_state.thread_id = tid
                    st.session_state.created_at = s.get("time_label", tid[:8])
                    st.session_state.messages = history
                    st.session_state.pending_image = None
                    st.session_state.img_menu_mode = None
                    st.session_state.input_counter += 1
                    st.rerun()
            else:
                st.button(label, key=f"session_{tid}", use_container_width=True, disabled=True)
        with col2:
            if st.session_state.delete_target == tid:
                if st.button("✅", key=f"confirm_{tid}", use_container_width=True):
                    delete_session(tid)
                    if is_current:
                        st.session_state.thread_id = str(uuid.uuid4())
                        st.session_state.created_at = _now_label()
                        st.session_state.messages = []
                        st.session_state.pending_image = None
                        st.session_state.img_menu_mode = None
                        st.session_state.input_counter += 1
                    st.session_state.delete_target = None
                    st.rerun()
            else:
                if st.button("🗑️", key=f"del_{tid}", use_container_width=True):
                    st.session_state.delete_target = tid
                    st.rerun()

    st.divider()
    st.markdown(f"""
    <div style="background: rgba(255,255,255,0.08); backdrop-filter: blur(10px); border-radius: 10px; padding: 8px 12px; margin-bottom: 8px;">
        <p style="color: #fff; font-size: 0.85rem; margin: 0; font-weight: 500;">� 当前对话</p>
        <p style="color: #fff; font-size: 0.95rem; margin: 4px 0 0; font-weight: 600;">{st.session_state.created_at}</p>
    </div>
    """, unsafe_allow_html=True)
    with st.expander("💡 帮助"):
        st.caption("1. 点输入框左侧「+」选择上传图片或粘贴链接\n2. AI 搜索菜谱并打分\n3. 多轮对话自动记忆\n4. 点击历史会话切换")

# ── 照片就绪提示 ─────────────────────────────────────────────
if st.session_state.pending_image is not None:
    st.toast("📷 图片已就绪，发送即附带", icon="✅")

# ── 当前对话名称 ──────────────────────────────────────────────
st.markdown(f"""
<div style="background: rgba(255,255,255,0.6); backdrop-filter: blur(10px); border-radius: 12px; padding: 10px 16px; margin-bottom: 12px; border: 1px solid rgba(210,180,140,0.2);">
    <span style="color: #D2691E; font-weight: 600; font-size: 1rem;">📝 当前对话：</span>
    <span style="color: #333; font-weight: 500; font-size: 1rem;">{st.session_state.created_at}</span>
</div>
""", unsafe_allow_html=True)

# ── 聊天记录 ──────────────────────────────────────────────────
st.markdown('<div class="chat-messages-area">', unsafe_allow_html=True)
for msg in st.session_state.messages:
    avatar = "🧑" if msg["role"] == "user" else "👨‍🍳"
    with st.chat_message(msg["role"], avatar=avatar):
        if msg.get("image"):
            st.image(msg["image"], width=300)
        if msg["content"]:
            st.markdown(msg["content"])
st.markdown('</div>', unsafe_allow_html=True)

# ── 底部固定输入区域：「+」按钮 + 输入框 + 发送按钮 ────────────
input_col1, input_col2, input_col3 = st.columns([1, 20, 1.5], gap="small")

with input_col1:
    img_pop = st.popover("+", use_container_width=True, help="添加图片")
    with img_pop:
        if st.session_state.pending_image is not None:
            st.image(st.session_state.pending_image, width=200)
            st.success("✅ 已就绪")
            if st.button("✕ 清除", use_container_width=True, key="clear_img"):
                st.session_state.pending_image = None
                st.session_state.img_menu_mode = None
                st.rerun()
            st.divider()

        mode = st.session_state.img_menu_mode
        if mode is None:
            st.markdown("<p style='text-align:center;color:#8C6A4A;font-weight:600;margin:0 0 0.3rem;'>添加图片</p>",
                        unsafe_allow_html=True)
            if st.button("📷 上传", use_container_width=True, key="opt_upload"):
                st.session_state.img_menu_mode = "upload"
                st.rerun()
            if st.button("🔗 链接", use_container_width=True, key="opt_url"):
                st.session_state.img_menu_mode = "url"
                st.rerun()
        elif mode == "upload":
            if st.button("‹ 返回", use_container_width=False, key="back_upload"):
                st.session_state.img_menu_mode = None
                st.rerun()
            uploaded = st.file_uploader("", type=["jpg","jpeg","png","webp"],
                label_visibility="collapsed", key="float_upload")
            if uploaded is not None:
                st.session_state.pending_image = uploaded.getvalue()
                st.session_state.img_menu_mode = None
                st.rerun()
        elif mode == "url":
            if st.button("‹ 返回", use_container_width=False, key="back_url"):
                st.session_state.img_menu_mode = None
                st.rerun()
            url = st.text_input("", placeholder="https://...",
                label_visibility="collapsed", key="float_url")
            if url.strip():
                st.session_state.pending_image = url.strip()
                st.session_state.img_menu_mode = None
                st.rerun()

with input_col2:
    user_text = st.text_input("消息输入", placeholder="输入食材清单或需求，发送消息...",
        label_visibility="collapsed", key=f"chat_input_{st.session_state.input_counter}")

with input_col3:
    send_btn = st.button("发送", use_container_width=True, type="primary")

# ── 将输入栏固定到底部（使用components.html注入可执行的JS） ──
components.html("""
<script>
    setTimeout(() => {
        const blocks = window.parent.document.querySelectorAll('[data-testid="stHorizontalBlock"]');
        if (blocks.length > 0) {
            blocks[blocks.length - 1].classList.add('fixed-input-bar');
        }
    }, 500);
</script>
""", height=0, width=0)

# 图片就绪时给「+」按钮加绿点徽标
if st.session_state.pending_image is not None:
    st.markdown("""
    <style>
    div[data-testid="stPopover"] > button::after {
        content: "" !important;
        position: absolute !important;
        top: 1px; right: 1px;
        width: 12px; height: 12px;
        background: #2ECC71 !important;
        border: 2px solid #fff !important;
        border-radius: 50% !important;
    }
    </style>
    """, unsafe_allow_html=True)

# ── 处理用户消息（回车或点击发送按钮） ────────────────────────
if send_btn or user_text:
    if not user_text and not st.session_state.pending_image:
        pass
    else:
        image_source = st.session_state.pending_image
        st.session_state.pending_image = None
        st.session_state.img_menu_mode = None
        st.session_state.input_counter += 1

        st.session_state.messages.append({"role": "user", "content": user_text or "", "image": image_source})

        with st.chat_message("user", avatar="🧑"):
            if image_source:
                st.image(image_source, width=300)
            if user_text:
                st.markdown(user_text)

        with st.chat_message("assistant", avatar="👨‍🍳"):
            with st.spinner("🔍 识别食材... 🔎 搜索菜谱... 🍳 生成推荐..."):
                messages = chat(
                    text=user_text or "",
                    image_source=image_source,
                    thread_id=st.session_state.thread_id,
                )
            ai_msgs = [m for m in messages if m.type == "ai" and hasattr(m, "content") and m.content]
            reply = ai_msgs[-1].content if ai_msgs else "抱歉，未能生成推荐，请换个食材试试。"
            st.markdown(reply)

        st.session_state.messages.append({"role": "assistant", "content": reply})
