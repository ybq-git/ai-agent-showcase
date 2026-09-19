"""验收测试：双 mock（假 adapter + 假 LLM），验证业务规则，不花钱。"""
import sys
sys.path.insert(0, ".")

from adapters.mock import MockAmazonAdapter
from ai.factory import FakeProvider
from modules.product_research import score_product, research_category


def _fake_llm_score(answer='{"competition_score": 7, "profit_potential": 8, "trend_score": 6, "overall_score": 7.2, "recommended": true, "tags": ["低竞争"], "analysis": "值得做"}'):
    return FakeProvider(answer=answer)


class TestScoreProduct:
    def test_maps_fields_correctly(self):
        product = MockAmazonAdapter().search_products("保温杯")[0]
        score = score_product(product, llm=_fake_llm_score())
        assert score.overall_score == 7.2
        assert score.recommended is True
        assert score.tags == ["低竞争"]
        assert score.asin == product.asin


class TestResearchCategory:
    def test_sorts_by_score_desc(self):
        scores = research_category("保温杯", limit=5, min_overall_score=6.0,
                                   llm=_fake_llm_score())
        assert len(scores) > 0
        order = [s.overall_score for s in scores]
        assert order == sorted(order, reverse=True)   # 从高到低

    def test_filters_below_threshold(self):
        scores = research_category("保温杯", limit=5, min_overall_score=8.0,
                                   llm=_fake_llm_score())
        assert scores == []   # 全部 7.2 分，门槛 8 分 → 全被过滤

    def test_unknown_category_returns_nothing(self):
        # 示例目录只有保温杯，查别的品类要返回空，不能拿保温杯冒充
        assert MockAmazonAdapter().get_best_sellers("瑜伽垫") == []
        assert research_category("瑜伽垫", llm=_fake_llm_score()) == []
