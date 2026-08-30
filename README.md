# AI Agent 作品集

**目标岗位**：深圳 AI Agent 应用开发工程师

我从零自学 AI Agent，下面是手写的 6 个项目。每个项目都有 README（怎么跑、技术点、我踩过的坑/评测数据），你能看到我从"调用 API"到"自己编排智能体"的完整成长线。

## 项目清单

### 1. 多智能体报告系统 [`MultiAgent_Report/`](./MultiAgent_Report/)

基于 LangGraph 编排「研究员 → 写作员 → 审核员」三个智能体，审核不通过就自动打回重写（最多 3 版），实现带质量控制的报告生成闭环；并用 FastAPI 封装成 `POST /report` 接口，任何前端都能调用整条流水线。

### 2. 深圳政策 RAG 问答系统 [`semantic_search_policy/`](./semantic_search_policy/)

把深圳人才/租房/落户政策文档喂进 RAG，问答**带引用溯源**，内置防幻觉 Prompt。自建 24 题评测集，两轮 chunk_size + k 消融实验把准确率从 **45.8% 提升到 58.3%**，并输出逐条失败分析和改进方向。

### 3. AI 私人厨师 [`AI_private_chef/`](./AI_private_chef/)

多模态智能推荐 Agent：传食材照片/清单 → qwen 多模态识别 → Tavily 联网搜菜谱 → 打分排序 → 输出带评分的菜谱报告，配 Streamlit 全栈界面、SQLite 多轮记忆。

### 4. AI 穿衣建议助手 [`weather_agent/`](./weather_agent/)

LangGraph 双节点工作流：高德天气 API 取实时天气 → 通义千问生成穿衣/带伞建议，用 `lru_cache` 优化重复调用，已部署到 Streamlit Cloud。

### 5. 简历优化生成器 [`resume_builder/`](./resume_builder/)

LLM 应用：解析 PDF/TXT 简历 → qwen 按 STAR 法则优化 + 提取技能词 → 套本地 Word 模板 AI 逐段填槽 → 输出 `.docx`，带多级 fallback。

### 6. 简历分析 Agent [`resume_analyst_agent/`](./resume_analyst_agent/)

LangGraph 双节点工作流：分析简历弱点 → 推荐针对性学习资源。推荐节点先让 LLM 生成检索关键词，再用 DuckDuckGo 搜**真实资源链接**；网络不可用时自动回退到纯模型生成，做到健壮不崩。

---

### 📦 [`archive/`](./archive/)

早期练手代码（ChromaDB 演示、贪吃蛇游戏、LangChain/原生对比练习、API 冒烟脚本等）存档区，不属于正式作品，仅留作学习轨迹。
