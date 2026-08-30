# 简历优化生成器

把一份 PDF / TXT 简历交给通义千问做 **STAR 法则改写 + 技能词提取**，再套用本地 Word 模板、由 AI 逐段填入，输出排版好的 `.docx`。

## 亮点

- **PDF 解析**：用 PyMuPDF（fitz）从 PDF 提取简历正文。
- **LLM 内容优化**：DashScope 调 qwen-max，按 STAR 法则改写经历、提取技能词。
- **Word 模板 + AI 填槽**：解析本地 `.docx` 模板（含文本框、表格）逐段填入；无合适模板时降级为从零生成一份简历，尽量保住排版。
- **工程化的 fallback**：文件格式转换（`.doc`→`.docx`）、模板选区、从零生成等多条兜底路径，不是一把梭。

## 技术栈

PyMuPDF · python-docx · DashScope（qwen-max）· python-dotenv · lxml

## 快速开始

1. 在目录下新建 `.env`，写入：
   ```
   DASHSCOPE_API_KEY=你的通义千问key
   ```
2. 安装依赖：
   ```bash
   pip install -r requirements.txt
   ```
3. 准备输入：把 PDF/TXT 简历放进可读位置，运行：
   ```bash
   python main.py <你的简历路径>
   ```

> `templates/`（Word 模板）、`output/`（结果）目录会在运行时创建；没有模板时会用从零生成降级模式。

## 目录结构

```
resume_builder/
├── main.py          # 主流水线：解析→Star优化→填模板→输出docx
├── qwen_client.py   # DashScope qwen-max 客户端
├── requirements.txt
├── templates/       # 运行时可选的 .docx 模板
└── output/          # 生成的成品简历
```
