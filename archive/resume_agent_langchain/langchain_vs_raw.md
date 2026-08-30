# LangChain重构对比
- 原生版本：约60行，包含手动拼接Prompt、处理API响应、清洗JSON
- LangChain版本：约40行，核心逻辑集中在模板定义和链调用，代码更清晰
- 优势：Prompt模板化，输出解析可复用，后续加memory或工具更容易
