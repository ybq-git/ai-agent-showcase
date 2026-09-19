# 跨境电商卖家运营 Agent

一个面向跨境电商卖家的 **AI 运营助手**：输入品类 → **AI 选品调研** → **AI 生成合规 Listing** → **质检循环收敛**。全程带 Hybrid RAG 证据链、安全治理（注入拦截 / PII 脱敏 / 工具白名单 / 写操作人工审批）、确定性评估。

> 业务场景：亚马逊卖家从"卖什么"到"怎么卖"的核心运营流程（选品 + Listing），不是客服。

---

## 一、快速体验

```bash
# 1. 启动 API（默认用假模型跑通全流程，不花钱）
uvicorn apps.api:app

# 2. 用真模型（需配置 DASHSCOPE_API_KEY）
$env:LLM_PROVIDER="qwen"    # PowerShell
uvicorn apps.api:app
```

浏览器打开 `http://127.0.0.1:8000/docs`，试 `POST /research`：

```json
{"category": "Insulated Water Bottle"}
```

返回 AI 打分排序后的选品推荐（综合分 / 是否推荐 / 中文分析）。

### 对话演示（更直观）

```bash
python chat_demo.py                        # 假模型免费跑通
$env:LLM_PROVIDER="qwen"; python chat_demo.py   # 真模型
```

支持指令：
- `帮我选品保温杯` → AI 选品调研
- `帮我写Listing` → 生成中文 Listing（硬校验 + 质检）
- `帮我写英文Listing` → 生成英文 Listing（输出语言由 `language` 参数控制，模板强约束不混语言）
- 质检不合格 → 自动带质检意见重写一版（保持用户指定语言）

## 二、架构

```
用户请求 → FastAPI
            │
            ▼
    [Safety Gate 安全门]           ← 注入拦截(Prompt Injection) + PII脱敏
            │
            ▼
    [LangGraph 编排]              ← 条件路由(intent→专家) 写死在代码
      ├── 选品专家: adapter拉商品 → LLM打分 → 排序/过滤
      └── Listing专家: LLM生成 → 质检(硬规则+LLM双层)
             │ 不合格 → 打回重写（revision_count 上限防死循环）
             ▼
    [Hybrid RAG 证据链]           ← 向量+BM25 → RRF融合 → 信任过滤 → 引用
            │
            ▼
    [写操作治理]                  ← 工具白名单裁剪 + 幂等查重 + 人工审批单
```

## 三、核心设计（5 个工程点）

### 1. LLM Provider 抽象层 + 输出稳定解析
`ai/base.py` + `ai/factory.py`：业务代码只依赖 `BaseLLMProvider` 接口，真模型（通义/kimi）与假模型（`FakeProvider`）可插拔——**换模型不改业务代码，测试用假人不烧钱**。`ai/parse.py` 的 `parse_llm_json` 容错解析：剥 markdown 代码块 → 提取 JSON → 类型校验，应对 LLM 输出的不稳定性。

### 2. 多智能体编排 + 白名单路由（LangGraph）
`graph/workflow.py`：LangGraph 状态图，条件路由（`route` 按 intent 分派到选品/Listing 专家）。**路由是代码硬边界，不是 prompt 软约束**——模型只能在白名单节点里走。质检不通过 → 回炉重写（cycle），`MAX_REVISIONS` 上限防死循环。

### 3. 安全治理三件套（`safety/`）
- **工具白名单**（`router.py`）：`plan(intent)` → 物理裁剪工具集，白名单外工具模型看都看不到。
- **写操作审批门**（`guard.py`）：上架/改价等写操作**只生成审批单**（`PENDING_HUMAN_APPROVAL`），由人工确认才执行；请求内容哈希做**幂等查重**，重复请求返回 `DUPLICATE_BLOCKED`。
- **SafeGuard**（`safeguard.py`）：prompt 注入正则拦截（fail-closed）+ 卡号/手机号/身份证 PII 脱敏。

### 4. 内容质检双层判定（`modules/quality.py`）
Listing 生成后：**硬规则层**（代码校验字符数/条数）+ **LLM 内容层**（审查是否编造规格、含关键词）。实测抓到过模型"编造 304 不锈钢、12h 保温等商品数据中不存在的规格"——这正是亚马逊封店风险源，质检门在上架前拦截。

### 5. Hybrid RAG 证据链 + 确定性评估（`rag/`）
- 双路召回：**向量检索**（通义 text-embedding-v3，语义）+ **BM25**（jieba 分词，精确匹配编号/SKU）
- **RRF 融合**：只看排名不调权重，两路都命中的文档顶到最前
- **信任过滤 + 预算打包 + 引用标注**：答案可溯源，防幻觉
- **指标评估**：MRR 与引用覆盖率，用数字说话而非"感觉"

## 四、评估报告

| 指标 | 结果 | 含义 |
|---|---|---|
| 检索 MRR | 1.000 | 5 个测试问题，正确答案全部排第 1 |
| 引用覆盖率 | 1.00 | 回答全部正确引用应引用的证据文档 |
| 单元测试 | 11 passed | 纯函数确定性断言（解析/校验/安全/幂等/RRF） |
| 验收测试 | 3 passed | 业务规则（双 mock，不烧钱） |

## 五、项目结构

```
cross_border_agent/
├── adapters/     # 平台适配：数据契约(dataclass) + MockAmazonAdapter（可换真 API）
├── ai/           # LLM 抽象层：BaseLLMProvider + Qwen/Fake + parse_llm_json
├── modules/      # 业务内核：选品打分 / Listing生成 / 质检
├── graph/        # LangGraph 编排：条件路由 + 质检回炉循环
├── safety/       # 治理：工具白名单 + 审批门/幂等 + 注入拦截/PII脱敏
├── rag/          # Hybrid RAG：分块/向量/BM25/RRF/信任过滤/评估
├── apps/         # FastAPI：/health /research /listing
└── tests/        # pytest：单元 + 验收（双 mock 不烧 LLM 钱）
```

## 六、运行测试

```bash
python -m pytest tests/ -v          # 单元 + 验收（全部用假 LLM，不花钱）
python rag/eval_retrieval.py        # 检索 MRR
```

## 七、环境变量

```bash
DASHSCOPE_API_KEY=你的通义key     # LLM + embedding
LLM_PROVIDER=fake|qwen           # fake=假模型跑通流程(默认) | qwen=真模型
QWEN_MODEL=qwen-max              # 可换 qwen-turbo(便宜) / kimi-k2.7-code 等
```
