"""
ChromaDB 基础操作：创建集合、添加文档、查询
"""
import os
os.environ["HF_ENDPOINT"] = "https://hf-mirror.com"

import chromadb
from chromadb.utils import embedding_functions

# 创建一个临时的本地Chroma客户端（数据保存在当前文件夹的chroma_db目录）
client = chromadb.PersistentClient(path="./chroma_db")

# 使用免费的sentence-transformers中文嵌入模型
embedding_func = embedding_functions.SentenceTransformerEmbeddingFunction(
    model_name="paraphrase-multilingual-MiniLM-L12-v2"
)

# 创建或获取一个集合（类似数据库中的表）
collection = client.get_or_create_collection(
    name="my_docs",
    embedding_function=embedding_func
)

# 添加文档：每条文档包含id、文本内容、可选的元数据
collection.add(
    documents=[
        "深圳今天天气晴朗，气温28摄氏度",
        "北京今天有雾霾，空气质量较差",
        "人工智能岗位需要掌握Python和机器学习"
    ],
    ids=["doc1", "doc2", "doc3"]
)
print("文档添加成功！")

# 查询：搜索与查询文本最相似的文档（返回最相似的2条）
results = collection.query(
    query_texts=["深圳的气候如何？"],
    n_results=2
)	
print("查询结果：")
print(results["documents"])  # 打印匹配到的文档列表
# 更新文档：修改id为doc3的内容
collection.update(
    ids=["doc3"],
    documents=["人工智能工程师需要掌握Python、深度学习框架和模型部署"]
)
# 删除文档：移除id为doc2的文档
collection.delete(ids=["doc2"])

# 再次查询，查看变化
results2 = collection.query(
    query_texts=["人工智能技能"],
    n_results=2
)
print("更新与删除后查询结果：", results2["documents"])
