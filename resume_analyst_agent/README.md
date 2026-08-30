# 简历分析 Agent（LangGraph）

上传一份简历 → 通义千问分析出 **3 个主要弱点** → 针对这些弱点推荐学习资源，并输出结构化 JSON。

## 亮点

- **LangGraph 双节点工作流**：`analyze`（找弱点）→ `recommend`（给资源），把"分析"和"给方案"拆成两个可复用的节点。
- **搜索增强 + 自动回退**：推荐节点先让 LLM 把弱点转成检索关键词，再用 DuckDuckGo 搜**真实资源链接**；当网络不可用（如国内访问 DDG 超时）时，自动回退到纯模型直接生成推荐，而**不会整个崩溃**。这是真实踩过的坑（见 `test_search.py` 里的注释）。
- **解析兜底**：对模型输出剥 markdown 代码块、截取第一段 `[` 到最后一个 `]` 再 `json.loads`——容忍大模型偶尔输出多余的废话。这个"AI 输出不稳要兜底"的经验在用大模型的项目里都适用。

## 技术栈

LangGraph（StateGraph）· 通义千问 qwen-max · duckduckgo_search · python-dotenv

## 快速开始

> 本项目**没有 `requirements.txt`**，需手动安装依赖：`langgraph`、`langchain-community`、`duckduckgo-search`、`dashscope`、`python-dotenv`。

1. 目录下新建 `.env`，写入：
   ```
   DASHSCOPE_API_KEY=你的通义千问key
   ```
2. 提供一份要分析的简历，命名为 `my_resume.txt`（放本目录）。
3. 运行：
   ```bash
   python career_agent_graph.py
   ```
   输出：弱点列表 + 总体建议 + 推荐资源（JSON）。

## 目录结构

```
resume_analyst_agent/
├── career_agent_graph.py      # 主图定义（StateGraph 两节点）
├── resume_analyst_agent.py    # node：分析简历弱点
├── resource_recommender_agent.py  # node：推荐学习资源（带搜索+回退）
├── test_search.py             # 搜索功能测试（演示回退）
└── my_resume.txt              # 输入简历（需自备）
```
