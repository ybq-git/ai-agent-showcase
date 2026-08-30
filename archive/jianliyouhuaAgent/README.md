# 简历优化 Agent（原生 API 版）

用 DashScope 直接调通义千问，把一段应届生经历按 **STAR 法则** 重写，并提取技能词，输出 JSON。

- 用原生 OpenAI 兼容接口 `call_qwen`（见 `test_qwen.py`）发请求，手写 prompt 模板。
- 产物：`resume_optimized.json`（STAR 改写 + 技能标签）。

**为什么在 archive**：这是"用原生 SDK 调大模型"的早期练习，也是简历主题的第一版。后来用 LangChain / LangGraph 分别重构（见同目录其它项目），正式前端已并入作品集项目 `resume_builder`。

## 怎么跑

1. 目录下新建 `.env`，写入 `DASHSCOPE_API_KEY=你的通义千问key`
2. `python resume_agent.py`（读 `my_resume.txt`，输出并保存 JSON）

## 文件

- `resume_agent.py` —— 主脚本：改写成 STAR + 提取技能，输出 JSON
- `skill_extractor.py` —— 技能词提取
- `test_qwen.py` —— `call_qwen` 封装（原生接口调用）
- `resume_prompt_design.txt` —— prompt 设计记录
- `my_resume.txt` / `resume_optimized.json` —— 输入/输出样例
