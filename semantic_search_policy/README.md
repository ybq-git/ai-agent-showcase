# 深圳政策 RAG 问答系统

把深圳的人才 / 租房 / 落户政策文档喂给 RAG，用自然语言问政策，答案**带引用来源**，并用** 24 题评测集**度量准确率。

## 它解决了什么

纯靠大模型"背"这种具体政策条款，容易编造。这个系统改成"**先去文档里检索到可靠依据，再让模型照着依据回答**"，并且回答必须标注引用了哪段文档。

## 亮点

- **完整 RAG 链路**：加载 txt/pdf → 分块 → 向量化（Embedding）→ 存 ChromaDB → 语义检索 → 通义千问按资料生成。
- **防幻觉 Prompt**：`如果无法从上下文中找到答案，就说你不知道，不要试图编造答案` —— 评测里模型确实会诚实地答"不知道"。
- **答案带引用溯源**：每个回答列出命中的文档块，可回查。
- **严谨评测**：自建 24 题评测集（数值/条件/是否/流程 四类），做两轮 `chunk_size + k` 消融实验，**45.8% → 58.3%**，输出逐条 fail 分析报告和下一步改进方向（否定式条款敏感度、FAQ 小段落召回、hybrid 检索、rerank）。

## 技术栈

LangChain（RetrievalQA）· ChromaDB · DashScope text-embedding-v2 · 通义千问 qwen-max · Streamlit · PyMuPDF

## 快速开始

1. 在目录下新建 `.env`，写入：
   ```
   DASHSCOPE_API_KEY=你的通义千问key
   ```
2. 安装依赖：
   ```bash
   pip install -r requirements.txt
   ```
3. 网页版：
   ```bash
   streamlit run app_rag_qa.py
   ```
   （或命令行版 `python policy_qa_agent_v2.py`，输入问题、`q` 退出）

> 知识库文档在 `docs_txt/`（可在 scripts 里切换加载方式），首次运行会自动建向量库到 `chroma_policy/`。

## 目录结构

```
semantic_search_policy/
├── policy_qa_agent_v2.py   # 主 agent：分块→向量化→Chroma→检索问答链
├── app_rag_qa.py           # Streamlit 网页版
├── pdf_loader.py           # PDF 文档加载
├── evaluate_rag.py         # 评测脚本
├── eval_questions.json     # 24 题评测集
├── evaluation_report.md    # 评测报告（含逐条 fail 分析）
├── evaluation_raw.json     # 评测原始结果
├── docs_txt/               # 政策文档（txt）
└── requirements.txt
```

## 评测结论（第二轮）

| 指标 | 上轮 (chunk=300, k=4) | 本轮 (chunk=500, k=6) |
|------|---------------------|---------------------|
| 准确率 | 45.8% | **58.3%** |
| 部分准确 | 8.3% | 4.2% |
| 不准确 | 45.8% | 37.5% |

调大 chunk、增大 k 让"下轮命中"了 4 题（如"次月到账""一年内申请期限"）；但仍有多题在否定式条款上漏检（文档写"不得，模型却说不知道"）。这也说明了 RAG 的边界：**检索召回决定了上限，模型只能在上限内尽力**。
