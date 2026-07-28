import streamlit as st
import os
from pdf_loader import extract_pdf_to_text
from policy_qa_agent_v2 import build_qa_chain_from_text

st.title("📘 深圳政策问答RAG系统")

# ---- 数据源选择 ----
DOCS_DIR = os.path.join(os.path.dirname(__file__), "docs_pdf")
builtin_pdfs = [f for f in os.listdir(DOCS_DIR) if f.endswith(".pdf")] if os.path.isdir(DOCS_DIR) else []

source_mode = st.radio("选择数据源", ["上传PDF"] + (["已有政策文件"] if builtin_pdfs else []), horizontal=True)

text = None

if source_mode == "已有政策文件":
    selected = st.selectbox("选择政策文件", builtin_pdfs)
    if selected:
        with st.spinner("加载PDF..."):
            text = extract_pdf_to_text(os.path.join(DOCS_DIR, selected))
        st.text_area("提取的文本预览", text[:500])
else:
    uploaded_file = st.file_uploader("上传政策PDF", type="pdf")
    if uploaded_file:
        text = extract_pdf_to_text(uploaded_file.read())
        st.text_area("提取的文本预览", text[:500])

# ---- 问答 ----
@st.cache_resource(show_spinner=False)
def get_chain(text: str):
    return build_qa_chain_from_text(text)

if text:
    with st.spinner("正在构建知识库（下载模型+向量化）..."):
        chain = get_chain(text)

    query = st.text_input("输入问题")
    if query:
        with st.spinner("思考中..."):
            result = chain({"query": query})
        st.write("**回答**", result["result"])

        with st.expander("📄 参考来源"):
            for i, doc in enumerate(result["source_documents"], 1):
                st.caption(f"#{i}  {doc.page_content[:200]}...")
