from dataclasses import dataclass,field

@dataclass
class ProductScore:
    asin:str
    title:str
    price:float
    review_count:int
    rating:float
    competition_score:float
    profit_potential:float
    trend_score:float
    overall_score:float
    recommended:bool
    tags:list[str]=field(default_factory=list)
    analysis:str=""
    
import json
from adapters.base import ProductListing
from ai.base import LLMMessage, BaseLLMProvider
from ai.factory import get_llm_provider
from ai.parse import parse_llm_json

SYSTEM_PROMPT = "你是一位资深跨境电商选品专家。根据商品的真实数据，从卖家角度打分。只输出 JSON，不要输出其他任何文字。"

SCORE_TEMPLATE = """请分析以下亚马逊商品，为新卖家打分：

商品数据：
{product_json}

只返回一个 JSON 对象，键必须是：
{{
  "competition_score": <float 0-10, 越低=竞争越小>,
  "profit_potential": <float 0-10, 越高=利润越好>,个？
  "trend_score": <float 0-10, 越高=更热>,
  "overall_score": <float 0-10 综合>,
  "recommended": <boolean>,
  "tags": <string 列表, 3-5个, 如 ["低竞争","高利润"]>,
  "analysis": <给卖家的2-3句分析>
}}

评分参考:
- competition_score: 评价数<200=低竞争(7-9), 评价数多=高竞争(2-4)
- profit_potential: 价格$15-$60=高利润(7-9)
- recommended: 当 overall_score>=6.5 且价格$15-$80 时为 true
"""


def score_product(product: ProductListing, llm: BaseLLMProvider | None = None) -> ProductScore:
    llm = llm or get_llm_provider()   # 没传就用工厂给的那个
    product_data = {
        "asin": product.asin,
        "title": product.title,
        "price_usd": product.price,
        "review_count": product.review_count,
        "rating": product.rating,
    }
    prompt = SCORE_TEMPLATE.format(product_json=json.dumps(product_data, ensure_ascii=False, indent=2))
    messages = [
        LLMMessage(role="system", content=SYSTEM_PROMPT),
        LLMMessage(role="user", content=prompt),
    ]
    raw = llm.complete(messages)
    data = parse_llm_json(raw.content)   # 用你 1.4 写的容错解析
    return ProductScore(
        asin=product.asin,
        title=product.title,
        price=product.price,
        review_count=product.review_count,
        rating=product.rating,
        competition_score=float(data.get("competition_score", 5)),
        profit_potential=float(data.get("profit_potential", 5)),
        trend_score=float(data.get("trend_score", 5)),
        overall_score=float(data.get("overall_score", 5)),
        recommended=bool(data.get("recommended", False)),
        tags=data.get("tags", []),
        analysis=data.get("analysis", ""),
    )
from adapters.mock import MockAmazonAdapter
from adapters.base import BasePlatformAdapter


def research_category(category: str, limit: int = 5, min_overall_score: float = 6.0,
                      adapter: BasePlatformAdapter | None = None,
                      llm: BaseLLMProvider | None = None) -> list[ProductScore]:
    adapter = adapter or MockAmazonAdapter()          # 没传就用 Mock，测试可换
    products = adapter.get_best_sellers(category, limit=limit)

    scores = []
    for product in products:
        try:
            score = score_product(product, llm=llm)   # 单个打分
            if score.overall_score >= min_overall_score:
                scores.append(score)                  # 过滤：只留综合分达标的
        except Exception:
            continue                                  # 单个失败不拖垮整批

    scores.sort(key=lambda s: s.overall_score, reverse=True)   # 从高到低排序
    return scores
