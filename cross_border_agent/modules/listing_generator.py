from dataclasses import dataclass,field
from adapters.base import ProductListing
from ai.base import LLMMessage, BaseLLMProvider
from ai.factory import get_llm_provider
from ai.parse import parse_llm_json
import json
@dataclass
class GeneratedListing:
    asin:str
    title:str
    bullet_points:list[str]
    description:str
    search_terms:list[str]
    seo_score:float
    character_counts:dict

SYSTEM_PROMPT = "你是一位资深的亚马逊 Listing 文案专家,擅长SEO。只输出 JSON,不要输出其他任何文字,如已有修改意见则附上。"

LISTING_TEMPLATE = """请为以下商品生成一份完整的亚马逊 Listing:

商品信息：
{product_json}

要求：
- 全文（标题、五点、描述、搜索词）一律用【{language}】撰写，不得混用其他语言
- title: 不超过 200 字符，自然包含主关键词
- bullet_points: 正好 5 条，每条以大写卖点标签开头，至少 20 字符
- description: 讲故事风格的产品描述
- search_terms: 后台搜索关键词列表（标题里没出现过的词）
- seo_score: 自评 SEO 质量 0-10

只返回一个 JSON 对象，键必须是：
{{
  "title": <string>,
  "bullet_points": [<string> × 5],
  "description": <string>,
  "search_terms": [<string>],
  "seo_score": <float>
}}
"""

def generate_listing(product, feedback: str = "", language: str = "中文", llm=None) -> GeneratedListing:
    llm = llm or get_llm_provider()   # 没传就用工厂给的真/假模型
    product_info = {"asin": product.asin, "title": product.title, "brand": product.brand,
                    "price": product.price, "rating": product.rating, "review_count": product.review_count,
                    "bullet_points": product.bullet_points, "description": product.description}
    prompt = LISTING_TEMPLATE.format(
    product_json=json.dumps(product_info, ensure_ascii=False, indent=2),
    language=language,
)
    if feedback:
        prompt += f"\n\n上次质检的修改意见，请逐条修正：\n{feedback}"
    messages = [
        LLMMessage(role="system", content=SYSTEM_PROMPT),
        LLMMessage(role="user", content=prompt),
    ]
    response = llm.complete(messages)
    data = parse_llm_json(response.content)

    title = data.get("title", "")
    description = data.get("description", "")

    return GeneratedListing(
        asin=product.asin,
        title=title,
        bullet_points=data.get("bullet_points", [])[:5],
        description=description,
        search_terms=data.get("search_terms", []),
        seo_score=float(data.get("seo_score", 0)),
        character_counts={
            "title": len(title),
            "description": len(description),
            "search_terms": len(" ".join(data.get("search_terms", []))),
        },
    )

def validate_listing(listing: GeneratedListing) -> list[str]:
    problems = []
    if len(listing.title) > 200:
        problems.append(f"标题超长: {len(listing.title)} 字符 (上限 200)")
    if len(listing.bullet_points) != 5:
        problems.append(f"五点描述应有 5 条，实际 {len(listing.bullet_points)} 条")
    for i, b in enumerate(listing.bullet_points, 1):
        if len(b) < 20:
            problems.append(f"第 {i} 条卖点太短: {len(b)} 字符 (最少 20)")
    return problems
