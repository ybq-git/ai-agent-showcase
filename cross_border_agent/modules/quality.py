from dataclasses import dataclass,field
from adapters.base import ProductListing
from ai.base import LLMMessage, BaseLLMProvider
from ai.factory import get_llm_provider
from ai.parse import parse_llm_json
from modules.listing_generator import validate_listing
import json
REVIEW_SYSTEM_PROMPT = "你是一位严格的亚马逊运营审核专家。你的任务是审查 Listing 文案的质量，判断它是否合格，并给出改进建议。只输出 JSON，不要输出其他任何文字。"

REVIEW_TEMPLATE = """请审查以下亚马逊 Listing 的质量。

原始商品信息：
{product_json}

生成的 Listing：
{listing_json}

审查标准：
1. 标题、五点、描述是否贴合商品本身（不夸大、不编造不存在的功能）
2. 五点描述是否有真实卖点（不是空话套话）
3. 标题是否自然包含商品的核心关键词
4. 整体文案是否有吸引力、能打动买家

只返回一个 JSON 对象，键必须是：
{{
  "content_ok": <boolean, true=内容质量合格，false=有明显问题>,
  "feedback": <一句话总评，说明为什么合格或不合格>,
  "suggestions": [<改进建议1>, <改进建议2>, ...]  // 合格时可为空列表
}}
"""


@dataclass
class QualityVerdict:
    passed:bool
    hard_issues:list[str]
    llm_feedback:str
    suggestions:list[str]




def review_listing(listing,product,llm=None):
    llm = llm or get_llm_provider()
    
    hard_issues = validate_listing(listing)
    product_info={"asin": product.asin, "title": product.title, "brand": product.brand,
                    "price": product.price, "rating": product.rating, "review_count": product.review_count,
                    "bullet_points": product.bullet_points, "description": product.description}
    listing_info = {"title": listing.title,
                     "bullet_points": listing.bullet_points,
                    "description": listing.description, "search_terms": listing.search_terms}
    prompt = REVIEW_TEMPLATE.format(
        product_json=json.dumps(product_info, ensure_ascii=False, indent=2),
        listing_json=json.dumps(listing_info, ensure_ascii=False, indent=2),
    )
    messages = [
        LLMMessage(role="system", content=REVIEW_SYSTEM_PROMPT),
        LLMMessage(role="user", content=prompt),
    ]
    data = parse_llm_json(llm.complete(messages).content)

    content_ok = bool(data.get("content_ok", True))
    passed = (len(hard_issues) == 0) and content_ok

    return QualityVerdict(
        passed=passed,
        hard_issues=hard_issues,
        llm_feedback=data.get("feedback", ""),
        suggestions=data.get("suggestions", []),
    )