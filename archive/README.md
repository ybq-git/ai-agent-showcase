# 📦 archive — 练手代码存档

这里是**早期练手代码**，不属于作品集正式项目，仅留作学习轨迹，不会出现在主页。

里面大多是：单文件 API / 框架冒烟测试（`llm_test.py`、`langchain_play.py`）、ChromaDB 演示（`chroma_db`）、纯 Pygame 小游戏（`sneke_game`）、以及"原生 vs LangChain vs LangGraph"渐进式的简历练习（`jianliyouhuaAgent`、`resume_agent_langchain`、`resume_analyst_agent`）、待办清单（`weekly_report`）。

每个文件夹都配了各自的 `README.md`；根目录 4 个散落的单文件脚本见下。

## 单文件练习脚本

- `app.py` —— mock Flask 接口（`POST /generate_report` 返回硬编码模拟周报），练手。
- `langchain_play.py` —— 一条 LangChain 翻译链 `prompt | llm | StrOutputParser`，认识链式调用。
- `llm_test.py` —— 用 OpenAI SDK 调 Kimi/Moonshot 的连通性冒烟测试。
- `copliot_tricks.py` —— 两个 Python 小工具（列表字符串反转、批量改文件名），Copilot 技巧练习。

想删除的话直接删 `archive/` 即可，不影响正式作品。
