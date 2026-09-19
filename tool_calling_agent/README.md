# 🔧 Tool Calling Agent

一个能自主调用外部工具的 AI 智能体，基于 **LangChain create_agent** + **阿里云千问 (qwen-max)**。

## 🎯 核心能力

用户用自然语言提问 → Agent 自主决定调用哪个工具 → 根据工具返回结果生成回复

## 🛠️ 可用工具

| 工具 | 功能 | 实现方式 |
|------|------|----------|
| `get_weather` | 查询城市天气 | 高德地图天气 API |
| `calculator` | 安全数学计算 | `ast` 白名单安全 eval |
| `web_search` | 联网搜索 | DuckDuckGo |
| `get_current_time` | 获取当前时间 | `datetime` 标准库 |

## 🏗️ 架构

```
用户输入
    │
    ▼
┌─────────────────────────────┐
│   LangChain create_agent    │
│   (基于 LangGraph 构建)      │
│                             │
│   LLM 判断 → 要调工具吗？    │
│     ├── 是 → 调用对应 tool   │← ReAct 循环
│     │        观察结果         │
│     │        继续判断...      │
│     └── 否 → 生成最终回复    │
└─────────────────────────────┘
    │
    ▼
回复用户
```

## 🚀 运行

```bash
pip install -r requirements.txt
streamlit run app.py
```

或命令行测试：

```bash
python -c "from agent import run; print(run('北京今天天气怎么样？'))"
```

## 📖 学习收获

- **Function Calling 原理**：理解 LLM 如何通过 Tool Schema（name/description/parameters JSON Schema）决策调用工具
- **ReAct 模式**：Thought → Action → Observation 的决策-执行-观察循环
- **Tool 定义**：`@tool` 装饰器、Pydantic 参数验证、安全计算
- **Agent 构建**：LangChain 1.3+ `create_agent` API（底层是 LangGraph StateGraph）

## 🔑 配置

在项目根目录 `.env` 中配置：

```bash
DASHSCOPE_API_KEY=your_key_here
AMAP_KEY=your_amap_key_here
```
