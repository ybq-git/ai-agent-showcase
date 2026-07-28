"""
深圳政策RAG问答Agent：
1. 加载本地txt文档并分割
2. 向量化存入Chroma
3. 使用LangChain的RetrievalQA链回答用户问题，并提示来源
4. build_qa_chain_from_text(text) — 供 Streamlit 调用
"""
import os

# ---------- 修复：国内网络使用 HF 镜像，必须在 import embeddings 前设置 ----------
os.environ.setdefault("HF_ENDPOINT", "https://hf-mirror.com")

from langchain_classic.chains import RetrievalQA
from langchain_classic.prompts import PromptTemplate
from langchain_community.vectorstores import Chroma
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.chat_models import ChatTongyi
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import DirectoryLoader, TextLoader
from langchain_core.documents import Document
from dotenv import load_dotenv

load_dotenv()

QA_CHAIN_PROMPT = PromptTemplate.from_template("""使用以下上下文来回答最后的问题。如果无法从上下文中找到答案，就说你不知道，不要试图编造答案。
始终使用中文回答。

上下文：
{context}

问题：{question}
有帮助的回答：""")


def build_qa_chain_from_text(text: str, chunk_size: int = 500, chunk_overlap: int = 50, k: int = 6):
    """从文本构建 RAG 问答链，供 Streamlit 等前端调用。

    Args:
        text: 原始文本内容
        chunk_size: 分块大小，默认 500
        chunk_overlap: 分块重叠，默认 50
        k: 检索返回的文档数，默认 6

    Returns:
        qa_chain: RetrievalQA 链对象，调用方式 qa_chain({"query": "你的问题"})
    """
    # 1. 文本分块
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=chunk_size, chunk_overlap=chunk_overlap)
    docs = text_splitter.split_documents([Document(page_content=text)])
    print(f"分块后文档数：{len(docs)}")

    # 2. 创建向量数据库（内存模式）
    embeddings = HuggingFaceEmbeddings(
        model_name="paraphrase-multilingual-MiniLM-L12-v2",
        model_kwargs={'device': 'cpu'}
    )
    vectordb = Chroma.from_documents(documents=docs, embedding=embeddings)

    # 3. 初始化千问模型
    qwen_api_key = os.getenv("DASHSCOPE_API_KEY")
    llm = ChatTongyi(model="qwen-max", dashscope_api_key=qwen_api_key)

    # 4. 构建检索问答链
    qa_chain = RetrievalQA.from_chain_type(
        llm=llm,
        chain_type="stuff",
        retriever=vectordb.as_retriever(search_kwargs={"k": k}),
        return_source_documents=True,
        chain_type_kwargs={"prompt": QA_CHAIN_PROMPT}
    )
    print("问答链构建完成")
    return qa_chain


# ---------- 本地测试 ----------
if __name__ == "__main__":
    base_dir = os.path.dirname(os.path.abspath(__file__))
    loader = DirectoryLoader(
        os.path.join(base_dir, "docs_txt"), glob="*.txt",
        loader_cls=TextLoader, loader_kwargs={"encoding": "utf-8"}
    )
    documents = loader.load()
    full_text = "\n\n".join(doc.page_content for doc in documents)
    print(f"加载了{len(documents)}份文档")

    chain = build_qa_chain_from_text(full_text)

    while True:
        query = input("\n请输入关于深圳政策的问题（输入q退出）：")
        if query.lower() == 'q':
            break
        result = chain({"query": query})
        print("\n回答：", result["result"])
        print("\n参考来源：")
        for doc in result["source_documents"]:
            source = doc.page_content[:100].replace("\n", " ")
            print(f" - {source}...")
