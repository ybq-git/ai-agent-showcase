from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from modules.product_research import research_category
from modules.listing_generator import generate_listing, validate_listing
from adapters.mock import MockAmazonAdapter
from safety.safeguard import detect_injection, mask_pii
from safety.guard import create_action_ticket
from rag.answer import ask as rag_ask

app = FastAPI(title="跨境电商卖家运营 Agent API")


# ===== 安全门：所有进入业务的文本都要先过这里 =====
def screen(text: str, field: str) -> str:
    """入口安全门：拦截 Prompt 注入；PII 打码后才放行。"""
    if detect_injection(text):
        raise HTTPException(status_code=403, detail=f"{field} 命中 Prompt 注入规则，已拦截")
    return mask_pii(text)


# ===== 请求体模型：告诉 FastAPI 前端会传什么 =====
class ResearchRequest(BaseModel):
    category: str            # "Insulated Water Bottle"

class ListingRequest(BaseModel):
    asin: str                # "B0WATER02"

class AskRequest(BaseModel):
    question: str            # "标题最多不能超过多少字符?"

class PublishRequest(BaseModel):
    asin: str                # 要上架的商品

# ===== 1. 健康检查（你已有）=====
@app.get("/health")
async def health():
    return {"status": "ok"}

# ===== 2. 选品：给个类目，返回排序好的推荐 =====
@app.post("/research")
async def research(req: ResearchRequest):
    category = screen(req.category, "category")
    scores = research_category(category, limit=4)
    return {
        "category": category,
        "count": len(scores),
        "products": [
            {"asin": s.asin, "title": s.title, "overall_score": s.overall_score,
             "recommended": s.recommended, "analysis": s.analysis}
            for s in scores
        ],
    }

# ===== 3. 生成 Listing：给个 ASIN，返回合规 Listing =====
@app.post("/listing")
async def listing(req: ListingRequest):
    asin = screen(req.asin, "asin")
    products = MockAmazonAdapter().search_products("保温杯")
    # 找不到就 404，别拿第一个商品冒充
    hero = next((p for p in products if p.asin == asin), None)
    if hero is None:
        raise HTTPException(
            status_code=404,
            detail=f"ASIN {asin} 不存在。可选：{[p.asin for p in products]}",
        )
    listing = generate_listing(hero)
    return {
        "asin": listing.asin,
        "title": listing.title,
        "bullet_points": listing.bullet_points,
        "description": listing.description,
        "character_counts": listing.character_counts,
        "validation": validate_listing(listing),   # 附带硬校验结果
    }

# ===== 4. 政策问答：Hybrid 检索（向量+BM25→RRF）→ 带引用作答 =====
@app.post("/ask")
async def ask_policy(req: AskRequest):
    question = screen(req.question, "question")
    return rag_ask(question, top_k=5)

# ===== 5. 上架：写操作只生成人工审批单，绝不直接执行 =====
@app.post("/publish")
async def publish(req: PublishRequest):
    asin = screen(req.asin, "asin")
    ticket = create_action_ticket("publish_listing", {"asin": asin})
    return {
        "status": ticket.status,          # PENDING_HUMAN_APPROVAL / DUPLICATE_BLOCKED
        "action": ticket.action,
        "target": ticket.target,
        "request_hash": ticket.request_hash,
        "created_at": ticket.created_at,
    }
