"""
深圳政策RAG问答Agent：
1. 加载本地txt文档并分割
2. 向量化存入Chroma
3. 使用LangChain的RetrievalQA链回答用户问题，并提示来源
"""
import os

# ---------- 修复：国内网络使用 HF 镜像，必须在 import embeddings 前设置 ----------
os.environ.setdefault("HF_ENDPOINT", "https://hf-mirror.com")

from langchain_classic.chains import RetrievalQA
from langchain_community.vectorstores import Chroma
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.chat_models import ChatTongyi
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import DirectoryLoader, TextLoader
from dotenv import load_dotenv

load_dotenv()
qwen_api_key = os.getenv("DASHSCOPE_API_KEY")

# 1. 加载txt文档
base_dir = os.path.dirname(__file__)
loader = DirectoryLoader(os.path.join(base_dir, "docs_txt"), glob="*.txt", loader_cls=TextLoader, loader_kwargs={"encoding": "utf-8"})
documents = loader.load()
print(f"加载了{len(documents)}份文档")

# 2. 文本分块
text_splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50)
docs = text_splitter.split_documents(documents)
print(f"分块后文档数：{len(docs)}")

# 3. 创建向量数据库（使用HuggingFace免费嵌入模型）
embeddings = HuggingFaceEmbeddings(
    model_name="paraphrase-multilingual-MiniLM-L12-v2",
    model_kwargs={'device': 'cpu'}
)
# 持久化存储到本地目录，避免每次重新计算
persist_directory = os.path.join(base_dir, "chroma_policy")
if not os.path.exists(persist_directory):
    vectordb = Chroma.from_documents(
        documents=docs,
        embedding=embeddings,
        persist_directory=persist_directory
    )
    vectordb.persist()
    print("向量库新建完成")
else:
    vectordb = Chroma(persist_directory=persist_directory, embedding_function=embeddings)
    print("加载已有向量库")

# 4. 初始化千问模型
llm = ChatTongyi(model="qwen-max", dashscope_api_key=qwen_api_key)

# 5. 构建检索问答链，返回源文档
qa_chain = RetrievalQA.from_chain_type(
    llm=llm,
    chain_type="stuff",
    retriever=vectordb.as_retriever(search_kwargs={"k": 3}),
    return_source_documents=True
)

# 6. 交互式问答
if __name__ == "__main__":
    while True:
        query = input("\n请输入关于深圳政策的问题（输入q退出）：")
        if query.lower() == 'q':
            break
        result = qa_chain({"query": query})
        print("\n回答：", result["result"])
        print("\n参考来源：")
        for doc in result["source_documents"]:
            print(f" - {doc.metadata.get('source', '未知')} : {doc.page_content[:100]}...")
