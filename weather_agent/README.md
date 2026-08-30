# AI 穿衣建议助手

输入城市名 → 高德天气 API 拿实时天气 → 通义千问生成穿扮 / 带伞建议，并记入历史。

已部署：https://ai-agent-showcase-dihml9trhspmktnnmoqsxy.streamlit.app/

## 亮点

- **LangGraph 双节点工作流**：`fetch_weather`（调高德 API）→ `suggest`（千问生成建议），把"取数"和"生成"拆成两个可复用的节点。
- **外部工具调用 API**：`httpx` 实时请求高德天气，拿到真实天气 JSON 再让模型生成，避免模型"凭感觉穿衣"。
- **`lru_cache` 优化**：同样的天气数据只调一次 LLM。代码里也诚实标注了注意点——LLM 输出非确定性，演示用缓存省 API 调用，生产应按"天气数据哈希 + 时间窗"设较短 TTL。
- **多环境密钥管理**：从 Streamlit Secrets 或 `.env` 读取 `DASHSCOPE_API_KEY` / `AMAP_KEY`，本地和 Streamlit Cloud 都能跑。

## 技术栈

LangGraph · 通义千问 qwen-max · 高德天气 API（httpx）· Streamlit · python-dotenv

## 快速开始

1. 在目录下新建 `.env`，写入：
   ```
   DASHSCOPE_API_KEY=你的通义千问key
   AMAP_KEY=你的高德web服务key
   ```
2. 安装依赖：
   ```bash
   pip install -r requirements.txt
   ```
3. 启动：
   ```bash
   streamlit run weather_app.py
   ```
   （或命令行版 `python weather_agent.py`——默认演示城市"吉安"）

## 目录结构

```
weather_agent/
├── weather_agent.py     # LangGraph 工作流 + 高德API + 千问建议
├── weather_app.py       # Streamlit 网页版
├── langgraph_demo.py    # 独立工作流演示
├── weather_agent_flow.png  # 工作流示意图
└── requirements.txt
```

## 部署到 Streamlit Cloud

在 Streamlit Cloud 的 Settings → Secrets 配置：
```
DASHSCOPE_API_KEY=你的key
AMAP_KEY=你的key
```
无需本地 `.env`，代码会自动走 `st.secrets`。
