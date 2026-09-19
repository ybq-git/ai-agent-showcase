import os
import json
from functools import lru_cache
from openai import OpenAI
from dotenv import load_dotenv

from ai.base import BaseLLMProvider, LLMMessage, LLMResponse

load_dotenv()
load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), "..", "..", ".env"))


class Provider(BaseLLMProvider):
    """真模型：通过 OpenAI 兼容端点调通义/kimi（kimi-k2.7-code 等）。"""

    def __init__(self, model: str = None):
        # 换模型：改 .env 里的 LLM_MODEL 即可，不用动代码
        model = model or os.getenv("LLM_MODEL") or os.getenv("QWEN_MODEL", "qwen-max")
        api_key = os.getenv("DASHSCOPE_API_KEY")
        if not api_key:
            raise RuntimeError("DASHSCOPE_API_KEY 环境变量未设置")
        self._client = OpenAI(
            api_key=api_key,
            base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
        )
        self._model = model

    def complete(self, messages: list[LLMMessage]) -> LLMResponse:
        resp = self._client.chat.completions.create(
            model=self._model,
            messages=[{"role": m.role, "content": m.content} for m in messages],
        )
        return LLMResponse(content=resp.choices[0].message.content)


# ---- 假模型的"剧本库"：按 prompt 关键词返回对应 JSON ----

# 选品打分：B0WATER04 给低分(会被过滤)，其余给不同高分，制造真实排序
_SCORE_SCRIPT = {
    "B0WATER01": {"competition_score": 6.0, "profit_potential": 6.5, "trend_score": 7.5, "overall_score": 6.8, "recommended": True, "tags": ["中等竞争", "口碑稳"], "analysis": "评价基数大，销量稳，适合稳健起步，但竞争已起。"},
    "B0WATER02": {"competition_score": 8.0, "profit_potential": 8.5, "trend_score": 7.0, "overall_score": 7.6, "recommended": True, "tags": ["低竞争", "高利润"], "analysis": "评价少、价格处黄金段，竞争小利润好，适合新手主推。"},
    "B0WATER03": {"competition_score": 3.5, "profit_potential": 7.0, "trend_score": 6.0, "overall_score": 6.3, "recommended": True, "tags": ["高评价数", "利润率中"], "analysis": "评价多但价格偏低，竞争激烈，利润率一般，谨慎跟进。"},
    "B0WATER04": {"competition_score": 7.5, "profit_potential": 4.0, "trend_score": 5.0, "overall_score": 5.4, "recommended": False, "tags": ["价格偏高", "受众窄"], "analysis": "价格高于黄金段，转化可能一般，暂不推荐。"},
}

# Listing 文案：按商品返回一份合规的
_LISTING_SCRIPT = {
    "B0WATER01": {"title": "Muye 500ml Insulated Bottle Stainless Steel Thermos Leak-Proof Hot 12H Cold 24H", "bullet_points": ["500ML VACUUM INSULATION: Double-wall stainless steel keeps drinks hot 12h and cold 24h.", "304 FOOD-GRADE STEEL: BPA-free lid, no metallic taste, safe for daily use.", "LEAK-PROOF LID: Screw lid with silicone seal, fits in car cup holder.", "SWEAT-FREE FINISH: Matte coating stays dry in hand, easy to clean.", "OFFICE & COMMUTE: Ideal companion for work, school and travel."], "description": "Muye insulated bottle keeps drinks at the right temperature all day. Food-grade 304 steel, leak-proof lid and a sweat-free matte body make it the reliable bottle for office, school and travel.", "search_terms": ["thermos cup", "travel mug", "stainless bottle"], "seo_score": 8.5},
    "B0WATER02": {"title": "RidgePace 1L Sports Water Bottle Double Wall Vacuum Stainless Steel Hot 12H Cold 24H", "bullet_points": ["1L LARGE CAPACITY: Double-wall vacuum body covers full-day hydration for gym and outdoor.", "HOT 12H / COLD 24H: 304 stainless steel keeps coffee hot and water cold for hours.", "BPA-FREE & LEAK-PROOF: Flip lid seals tight; fits standard car cup holder.", "DISHWASHER SAFE: Matte easy-grip finish, simple to clean after workouts.", "GYM, HIKE & OFFICE: One bottle for training, travel and desk days."], "description": "RidgePace 1L sports bottle with double-wall vacuum insulation keeps water cold 24h and coffee hot 12h. 304 stainless steel interior and a leak-proof flip lid make it a gym, hiking and office companion.", "search_terms": ["gym bottle", "insulated flask", "workout water bottle"], "seo_score": 8.8},
    "B0WATER03": {"title": "WarmGo 350ml Travel Coffee Cup Double Wall Insulated Slim Cup Holder Compatible", "bullet_points": ["SLIM 350ML BODY: Fits every standard cup holder, easy to carry.", "DOUBLE-WALL VACUUM: Keeps coffee hot 6h and iced drinks cold 12h.", "304 STAINLESS STEEL: BPA-free inner, no plastic taste.", "ONE-HAND SLIDE LID: Slide-lock sip opening for driving and desk.", "DAILY COFFEE & TEA: Perfect for commute, office and road trips."], "description": "WarmGo 350ml travel cup with slim double-wall body fits any cup holder. Slide-lock lid for one-hand drinking; 304 stainless steel interior keeps coffee hot 6h and iced drinks cold 12h.", "search_terms": ["coffee travel mug", "commute cup", "insulated tumbler"], "seo_score": 8.6},
    "B0WATER04": {"title": "Summit 1.5L Large Thermos Insulated Camping Flask Hot 24H Cold 48H", "bullet_points": ["1.5L BIG CAPACITY: Family-size hydration for camping and road trips.", "HOT 24H / COLD 48H: Long-lasting vacuum insulation for multi-day trips.", "DURABLE STEEL BODY: Powder-coated shell resists scratches and drops.", "WIDE MOUTH: Easy to fill with ice cubes and clean thoroughly.", "CARRY STRAP INCLUDED: Handle and strap for easy transport."], "description": "Summit 1.5L thermos built for camping and road trips. Powder-coated steel keeps drinks hot 24h or cold 48h, with a wide mouth for ice cubes and a carry strap for easy transport.", "search_terms": ["camping thermos", "large vacuum flask", "outdoor jug"], "seo_score": 8.2},
}

# Listing 文案中文版：prompt 要求【中文】时返回，避免"要中文却吐英文"
_LISTING_SCRIPT_ZH = {
    "B0WATER01": {"title": "慕野 500ml 不锈钢保温杯 双层真空 防漏杯盖 保温12小时 保冷24小时", "bullet_points": ["500ML 真空保温：双层不锈钢内胆，热饮保温12小时、冷饮保冷24小时。", "304 食品级不锈钢：杯盖不含BPA，无异味，日常饮用放心。", "防漏螺旋盖：硅胶密封圈锁紧，可放入车载杯架。", "磨砂防滑外壳：手感干爽不打滑，日常清洗方便。", "办公与通勤：上班、上学、出差都适用的随行保温杯。"], "description": "慕野500ml保温杯全天锁温。食品级304不锈钢内胆搭配防漏杯盖，磨砂杯身干爽好握，是办公、通勤和出行的可靠选择。", "search_terms": ["保温杯", "随行杯", "不锈钢水杯"], "seo_score": 8.5},
    "B0WATER02": {"title": "RidgePace 1L 运动水壶 双层真空保温 304不锈钢 保温12小时 保冷24小时", "bullet_points": ["1L 大容量：双层真空壶身，满足健身与户外全天补水需求。", "保温12小时 / 保冷24小时：304不锈钢内胆，咖啡保温、饮水保冷。", "不含BPA 防漏设计：翻盖密封严实，适配标准车载杯架。", "可机洗：磨砂易握表面，运动出汗后清洁起来也省事。", "健身、徒步、办公：训练、旅行、办公一瓶搞定。"], "description": "RidgePace 1L 运动水壶采用双层真空保温，保冷24小时、保温12小时。304不锈钢内胆配防漏翻盖，是健身、徒步和办公场景的补水伴侣。", "search_terms": ["运动水壶", "保温壶", "健身水杯"], "seo_score": 8.8},
    "B0WATER03": {"title": "WarmGo 350ml 随行咖啡杯 双层真空保温 纤细杯身 适配车载杯架", "bullet_points": ["350ML 纤细杯身：适配各类标准车载杯架，随身易带。", "双层真空：咖啡保温6小时，冷饮保冷12小时。", "304 不锈钢：内胆不含BPA，不留塑料味。", "单手滑盖：滑锁式饮水口，开车和办公都好用。", "日常咖啡与茶：通勤、办公、自驾的常备杯。"], "description": "WarmGo 350ml 随行杯纤细双层杯身适配任何杯架。滑锁杯盖单手饮水，304不锈钢内胆让咖啡保温6小时、冷饮保冷12小时。", "search_terms": ["咖啡随行杯", "通勤杯", "保温马克杯"], "seo_score": 8.6},
    "B0WATER04": {"title": "Summit 1.5L 大容量保温壶 户外露营 保温24小时 保冷48小时", "bullet_points": ["1.5L 大容量：家庭装补水，露营与自驾都够用。", "保温24小时 / 保冷48小时：长效真空保温，多日出行无忧。", "耐用钢制壶身：粉末涂层抗刮擦、耐磕碰，户外用更放心。", "广口设计：放冰块、加料和彻底清洗都很方便。", "附赠提手背带：握把加背带，装满水提着也不费力。"], "description": "Summit 1.5L 保温壶专为露营与自驾打造。粉末涂层钢制壶身保温24小时或保冷48小时，广口可放冰块，背带携带方便。", "search_terms": ["露营保温壶", "大容量保温瓶", "户外水壶"], "seo_score": 8.2},
}

# 质检：永远判合格(让演示能看到"通过")
_REVIEW_SCRIPT = {"content_ok": True, "feedback": "文案贴合商品真实规格，无编造，关键词覆盖良好，内容质量合格。", "suggestions": []}


def _extract_asin(text: str) -> str | None:
    """从 prompt 文本里抓 asin（打分和 Listing 的 prompt 都带商品 asin）。"""
    import re
    m = re.search(r'"asin"\s*:\s*"([^"]+)"', text)
    return m.group(1) if m else None


class FakeProvider(BaseLLMProvider):
    """假模型：不真调 API。按 prompt 关键词返回预置 JSON，让全流程免费跑通。"""

    def __init__(self, answer: str | None = None):
        # answer=None(默认) → 走剧本;传了 answer → 测试用它固定输出
        self.answer = answer

    def complete(self, messages: list[LLMMessage]) -> LLMResponse:
        # 显式传了 answer：测试要固定输出，不走剧本
        if self.answer is not None:
            return LLMResponse(content=self.answer)

        user_text = " ".join(m.content for m in messages)

        # 1) 打分 prompt（含 "competition_score"）
        if "competition_score" in user_text:
            asin = _extract_asin(user_text)
            script = _SCORE_SCRIPT.get(asin)
            if script:
                return LLMResponse(content=json.dumps(script, ensure_ascii=False))
            return LLMResponse(content=json.dumps(_SCORE_SCRIPT["B0WATER02"], ensure_ascii=False))

        # 2) Listing prompt（含 "seo_score"）
        if "seo_score" in user_text:
            asin = _extract_asin(user_text)
            scripts = _LISTING_SCRIPT_ZH if "中文" in user_text else _LISTING_SCRIPT
            script = scripts.get(asin)
            if script:
                return LLMResponse(content=json.dumps(script, ensure_ascii=False))
            return LLMResponse(content=json.dumps(scripts["B0WATER02"], ensure_ascii=False))

        # 3) 质检 prompt（含 "content_ok"）
        if "content_ok" in user_text:
            return LLMResponse(content=json.dumps(_REVIEW_SCRIPT, ensure_ascii=False))

        # 4) 其他：兜底返回固定话
        return LLMResponse(content="这是一个模拟的回答。")


@lru_cache(maxsize=1)
def get_llm_provider() -> BaseLLMProvider:
    provider = os.getenv("LLM_PROVIDER", "fake")
    if provider == "fake":
        return FakeProvider()
    if provider == "qwen":
        return Provider()
    raise ValueError(f"未知的 LLM_PROVIDER: {provider}")
