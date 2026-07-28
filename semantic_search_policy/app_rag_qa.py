import streamlit as st
from pdf_loader import extract_pdf_to_text
from policy_qa_agent_v2 import build_qa_chain_from_text

st.title("📘 深圳政策问答RAG系统")

uploaded_file = st.file_uploader("上传政策PDF", type="pdf")

@st.cache_resource(show_spinner=False)
def get_chain(text: str):
    return build_qa_chain_from_text(text)

if uploaded_file:
    # 只在文件内容变化时重建 chain
    file_bytes = uploaded_file.read()
    text = extract_pdf_to_text(file_bytes)

    st.text_area("提取的文本预览", text[:500])

    with st.spinner("正在构建知识库（下载模型+向量化）..."):
        chain = get_chain(text)

    query = st.text_input("输入问题")
    if query:
        with st.spinner("思考中..."):
            result = chain({"query": query})
        st.write("**回答**", result["result"])
        st.write("**来源**", result["source_documents"])
