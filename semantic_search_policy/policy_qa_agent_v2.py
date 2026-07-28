"""
深圳政策RAG问答Agent：
1. 加载本地txt文档并分割
2. 向量化存入Chroma
3. 使用LangChain的RetrievalQA链回答用户问题，并提示来源
4. build_qa_chain_from_text(text) — 供 Streamlit 调用
"""
import os
from dotenv import load_dotenv

load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), "..", ".env"), override=True)

from langchain_classic.chains import RetrievalQA
from langchain_classic.prompts import PromptTemplate
from langchain_community.vectorstores import Chroma
from langchain_community.embeddings import DashScopeEmbeddings
from langchain_community.chat_models import ChatTongyi
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import DirectoryLoader, TextLoader
from langchain_core.documents import Document

QA_CHAIN_PROMPT = PromptTemplate.from_template("""使用以下上下文来回答最后的问题。如果无法从上下文中找到答案，就说你不知道，不要试图编造答案。
始终使用中文回答。

上下文：
{context}

问题：{question}
有帮助的回答：""")

MAP_PROMPT = PromptTemplate.from_template("""使用以下上下文来回答部分问题。如果无法从上下文中找到答案，就说你不知道。

上下文：
{context}

部分问题：{question}
部分回答：""")

COMBINE_PROMPT = PromptTemplate.from_template("""使用以下总结的答案来回答最终的问题。如果无法从上下文中找到答案，就说你不知道，不要试图编造答案。
始终使用中文回答。

上下文总结：
{summaries}

最终问题：{question}
有帮助的回答：""")


CHROMA_DIR = os.path.join(os.path.dirname(__file__), "chroma_policy")


def build_qa_chain_from_text(text: str, chunk_size: int = 500, chunk_overlap: int = 50,
                            k: int = 6, chain_type: str = "stuff",
                            force_rebuild: bool = False):
    """从文本构建 RAG 问答链，供 Streamlit 等前端调用。

    向量库持久化到 chroma_policy/，不存在或 force_rebuild=True 时自动重建。

    Args:
        text: 原始文本内容
        chunk_size: 分块大小，默认 500
        chunk_overlap: 分块重叠，默认 50
        k: 检索返回的文档数，默认 6
        chain_type: RetrievalQA 链类型，默认 "stuff"；长文档时可用 "map_reduce"
        force_rebuild: 强制重建向量库，默认 False

    Returns:
        qa_chain: RetrievalQA 链对象，调用方式 qa_chain({"query": "你的问题"})
    """
    # 1. 文本分块
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=chunk_size, chunk_overlap=chunk_overlap)
    docs = text_splitter.split_documents([Document(page_content=text)])
    print(f"分块后文档数：{len(docs)}")

    # 2. 创建/复用向量数据库（持久化到 chroma_policy）
    embeddings = DashScopeEmbeddings(
        model="text-embedding-v2",
        dashscope_api_key=os.getenv("DASHSCOPE_API_KEY")
    )
    vectordb = _get_or_rebuild_vectordb(docs, embeddings, force_rebuild)

    # 3. 初始化千问模型
    qwen_api_key = os.getenv("DASHSCOPE_API_KEY")
    llm = ChatTongyi(model="qwen-max", dashscope_api_key=qwen_api_key)

    # 4. 构建检索器
    search_kwargs = {"k": k}

    # 5. 构建检索问答链（stuff 用 prompt，map_reduce 用 question_prompt+combine_prompt）
    if chain_type == "map_reduce":
        qa_chain = RetrievalQA.from_chain_type(
            llm=llm,
            chain_type="map_reduce",
            retriever=vectordb.as_retriever(search_kwargs=search_kwargs),
            return_source_documents=True,
            chain_type_kwargs={"question_prompt": MAP_PROMPT, "combine_prompt": COMBINE_PROMPT},
        )
    else:
        qa_chain = RetrievalQA.from_chain_type(
            llm=llm,
            chain_type="stuff",
            retriever=vectordb.as_retriever(search_kwargs=search_kwargs),
            return_source_documents=True,
            chain_type_kwargs={"prompt": QA_CHAIN_PROMPT},
        )
    print(f"问答链构建完成（chain_type={chain_type}, k={k}）")
    return qa_chain


def _get_or_rebuild_vectordb(docs, embeddings, force_rebuild=False):
    """获取向量数据库，不存在或无文档时自动重建。"""
    if force_rebuild or not os.path.isdir(CHROMA_DIR):
        if force_rebuild and os.path.isdir(CHROMA_DIR):
            import shutil
            shutil.rmtree(CHROMA_DIR)
            print("已删除旧向量库，重新构建...")
        os.makedirs(CHROMA_DIR, exist_ok=True)
        vectordb = Chroma.from_documents(
            documents=docs, embedding=embeddings,
            persist_directory=CHROMA_DIR,
        )
        print(f"向量库已新建到 {CHROMA_DIR}，{len(docs)} 个文档块")
        return vectordb
    vectordb = Chroma(
        persist_directory=CHROMA_DIR,
        embedding_function=embeddings,
    )
    exist_count = vectordb._collection.count()
    if exist_count == 0:
        vectordb = Chroma.from_documents(
            documents=docs, embedding=embeddings,
            persist_directory=CHROMA_DIR,
        )
        print(f"向量库为空，已重建，{len(docs)} 个文档块")
    else:
        print(f"向量库已存在（{exist_count} 个文档块），直接复用")
    return vectordb


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
