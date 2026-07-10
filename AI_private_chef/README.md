# 👨‍🍳 私人厨师 · AI 智能食谱推荐系统

上传食材照片或输入食材清单，AI 识别食材后联网搜索菜谱，按营养和难度打分排序，输出结构化推荐报告。

## 🚀 快速开始

### 1. 获取 API Key

- **DashScope**（阿里云）：注册 [dashscope.aliyuncs.com](https://dashscope.aliyuncs.com)，获取 API Key，用于调用 Qwen 多模态模型
- **Tavily Search**：注册 [tavily.com](https://tavily.com)，获取 API Key，用于联网搜索菜谱

### 2. 配置环境变量

```bash
cp .env.example .env
# 编辑 .env，填入 DASHSCOPE_BASE_URL、DASHSCOPE_API_KEY、TAVILY_API_KEY
```

### 3. 安装依赖

```bash
pip install -r requirements.txt
```

### 4. 运行

**Streamlit 前端（推荐）**：

```bash
streamlit run app.py
```

浏览器打开 `http://localhost:8501`，上传食材照片或输入食材清单即可。

**命令行 Demo**：

```bash
python private_chef.py
```

## 📁 文件结构

```
AI_private chef/
├── agent.py          # 后端核心：LLM 初始化、Agent 创建、对话调用
├── app.py            # Streamlit 前端
├── private_chef.py   # 命令行 Demo
├── requirements.txt  # Python 依赖
├── .env.example      # 环境变量模板（复制为 .env）
└── README.md         # 本文件
```

## 🔧 技术栈

- **LangChain + LangGraph**：Agent 编排与对话状态管理
- **Qwen3.5-plus（DashScope）**：多模态食材识别与食谱生成
- **Tavily Search**：联网实时搜索菜谱
- **Streamlit**：Web 前端界面
- **SQLite**：对话历史持久化

## ⚠️ 注意事项

- `.env` 文件包含 API Key，请勿上传到公开仓库
- 首次运行会自动创建 `resources/personal_chef.db` 数据库文件
- 命令行 Demo 需从 `AI_private chef/` 目录运行，否则路径可能出错
- API Key 消费按用量计费，请注意用量
