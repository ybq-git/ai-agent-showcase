"""
读取docs文件夹下的政策文档，做向量化存储，然后进行语义查询。
"""
import chromadb
from chromadb.utils import embedding_functions
import os

# ---------- 修复：国内网络使用 HF 镜像，避免 huggingface.co 连不上 ----------
os.environ.setdefault("HF_ENDPOINT", "https://hf-mirror.com")

# 初始化
client = chromadb.PersistentClient(path=os.path.join(os.path.dirname(__file__), "policy_db"))
embedding_func = embedding_functions.SentenceTransformerEmbeddingFunction(
    model_name="paraphrase-multilingual-MiniLM-L12-v2"
)
collection = client.get_or_create_collection(
    name="shenzhen_policy",
    embedding_function=embedding_func
)

# 读取文档文件夹中的txt文件
docs_folder = "docs"
documents = []
metadatas = []
ids = []
for i, filename in enumerate(os.listdir(docs_folder)):
    if filename.endswith(".txt"):
        with open(os.path.join(docs_folder, filename), "r", encoding="utf-8") as f:
            content = f.read()
            documents.append(content)
            metadatas.append({"source": filename})
            ids.append(f"doc_{i}")

if documents:
    # 先清空集合再添加，避免重复写入
    existing_ids = collection.get()["ids"]
    if existing_ids:
        collection.delete(ids=existing_ids)
    collection.add(documents=documents, metadatas=metadatas, ids=ids)
    print(f"成功写入{len(documents)}份文档")

    # 测试查询
    query = "应届生能拿多少租房补贴？"
    result = collection.query(query_texts=[query], n_results=1)
    print(f"查询：{query}")
    print(f"最相关文档：{result['documents'][0]}")
else:
    print("docs文件夹内无txt文件")
