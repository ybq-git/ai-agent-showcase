# 简历优化 Agent（LangChain 版）

同一个 STAR 简历改写，改用 **LangChain 链** 重构：`resume_prompt | llm | StrOutputParser`，代码更短、更强植。

- 对比文件 `langchain_vs_raw.md` 记录了"原生 API vs LangChain 链"的差别与取舍。

**为什么在 archive**：这是"用大模型框架重构手写代码"的学习对比练习，功能与 `jianliyouhuaAgent` 重复；正式的简历生成前端已并入作品集项目 `resume_builder`。

## 怎么跑

1. 目录下新建 `.env`，写入 `DASHSCOPE_API_KEY=你的通义千问key`
2. `python resume_agent_langchain.py`（读 `my_resume.txt`，输出优化后的 JSON）

## 文件

- `resume_agent_langchain.py` —— 用 LangChain `ChatPromptTemplate | ChatTongyi | StrOutputParser` 实现
- `langchain_vs_raw.md` —— 原生 SDK vs LangChain 链的对比笔记
- `my_resume.txt` —— 输入样例
