# 简历分析 Agent（LangGraph 版）

用 **LangGraph 两节点图** 串起来：`analyze`（找简历弱点）→ `recommend`（推荐学习资源，带搜索、搜索超时会回退纯模型生成）。

- `career_agent_graph.py` 是主图；`resume_analyst_agent.py` / `resource_recommender_agent.py` 是两个节点函数。
- 代码中注明了国内网络搜索易超时、已做回退——是真实遇到过的坑。

**为什么在 archive**：小型 LangGraph 练手，功能与简历主题重复，不单独作为作品集项目。

## 怎么跑

1. 目录下新建 `.env`，写入 `DASHSCOPE_API_KEY=你的通义千问key`
2. `python career_agent_graph.py`（读 `my_resume.txt`，输出弱点 + 建议 + 资源）

## 文件

- `career_agent_graph.py` —— 主图定义（StateGraph）
- `resume_analyst_agent.py` —— node：分析弱点
- `resource_recommender_agent.py` —— node：推荐学习资源
- `test_search.py` —— 搜索功能测试
- `my_resume.txt` —— 输入样例
