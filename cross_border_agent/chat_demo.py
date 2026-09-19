"""对话版演示：像聊天一样驱动选品/Listing Agent。"""
import os
import sys

sys.stdout.reconfigure(encoding="utf-8")

from adapters.mock import MockAmazonAdapter
from modules.listing_generator import validate_listing
from graph.workflow import workflow
from safety.safeguard import detect_injection, mask_pii

WELCOME = """跨境电商卖家运营 Agent（对话版）
=============================================
你可以说:
  1. "帮我选品/调研 保温杯"     → AI 选品调研
  2. "帮我写 Listing B0WATER02"  → 生成 + 质检 Listing
  3. "退出" 结束
============================================="""

# 工作流节点 → 中文标签，用于打印执行轨迹
NODE_LABEL = {"research": "选品调研", "generate": "生成 Listing", "review": "质检"}


def run_workflow(intent: str, **kw) -> dict:
    """把一次请求交给 LangGraph 工作流执行，顺带打印节点轨迹。

    意图路由、质检回炉（上限 3 版）都在图里，这里只负责喂初始状态、收最终状态。
    """
    state = {
        "intent": intent, "category": "", "scores": [], "language": "中文",
        "hero": None, "listing": None, "feedback": "",
        "revision_count": 0, "passed": False,
    }
    state.update(kw)

    final = dict(state)
    print("  工作流:", end=" ")
    for chunk in workflow.stream(state):
        for node, update in chunk.items():
            print(f"[{NODE_LABEL.get(node, node)}]", end=" ")
            if update:
                final.update(update)
    print()
    return final

def parse_intent(text: str) -> tuple[str, str]:
    """解析用户输入 → (意图, 关键词)。规则优先,复杂再上 LLM。"""
    text = text.strip()

    # 先看意图关键词
    if any(w in text for w in ["选品", "调研", "看看", "推荐商品", "research", "选什么"]):
        # 取意图词后面说的品类；没说就反问，不写死默认值
        import re
        m = re.search(r"(?:选品|调研|看看|推荐商品|research|选什么)\s*(.+)", text)
        category = m.group(1).strip() if m else ""
        if not category:
            return "research_no_category", "", "中文"
        return "research", category, "中文"

    if any(w in text for w in ["listing", "写", "生成", "文案", "五点"]):
        # 提取 asin:找 B0 开头的商品号
        import re
        m = re.search(r"B0[A-Z0-9]+", text.upper())
        # 识别语言:用户说"英文/english/en"就英文,否则中文
        language = "英文" if any(w in text.lower() for w in ["英文", "english", " en", "用en"]) else "中文"
        # 没指定商品就反问，不替用户瞎猜
        if not m:
            return "listing_no_asin", "", language
        return "listing", m.group(0), language


    return "unknown", "", "中文"

def handle(intent: str, keyword: str, language: str = "中文"):

    """按意图调用业务模块:选品调研 or 生成+质检 Listing。"""
    if intent == "listing_no_asin":
        lang = "英文" if language == "英文" else ""
        print(f"\n要写哪个商品的{lang} Listing？请指定 ASIN：")
        for p in MockAmazonAdapter().search_products("保温杯"):
            print(f"  {p.asin}  {p.title}")
        print(f"  例如：帮我写{lang}Listing B0WATER02")
        return

    if intent == "research_no_category":
        print("\n要调研哪个品类？例如：帮我选品保温杯")
        return

    if intent == "research":
        print(f"\n【AI 选品调研中... 品类: {keyword}】")
        if not MockAmazonAdapter().get_best_sellers(keyword):
            print(f"示例目录里没有「{keyword}」这个品类，目前只有保温杯类商品。")
            return
        scores = run_workflow("research", category=keyword)["scores"]
        if not scores:
            print("找到商品了，但综合分都没过 6.0 的门槛")
            return
        print(f"找到 {len(scores)} 个推荐,按综合分排序:")
        for s in scores:
            print(f"\n  {s.overall_score:.1f}分 | {s.title}")
            print(f"      竞争 {s.competition_score:.1f} | 利润 {s.profit_potential:.1f} | 趋势 {s.trend_score:.1f}")
            print(f"      推荐: {'是' if s.recommended else '否'} | 标签: {', '.join(s.tags)}")
            # 模型有时返回列表，拼成一句话，别把 Python 的 [] 打到界面上
            analysis = s.analysis if isinstance(s.analysis, str) else " ".join(s.analysis)
            print(f"      分析: {analysis}")

    elif intent == "listing":
        # 找到 asin 对应的商品
        products = MockAmazonAdapter().search_products("保温杯")
        hero = next((p for p in products if p.asin == keyword), products[0])
        print(f"\n【为 {hero.title} 生成 {language} Listing...】")


        # 生成 → 质检 → 不合格回炉重写（上限 3 版），全在 LangGraph 图里跑
        out = run_workflow("listing", hero=hero, language=language)
        listing = out["listing"]

        print(f"\n标题({listing.character_counts['title']}字符):")
        print(f"  {listing.title}")
        print("\n五点描述:")
        for i, b in enumerate(listing.bullet_points, 1):
            print(f"  {i}. {b}")
        desc_len = listing.character_counts.get("description", len(listing.description))
        print(f"\n商品描述({desc_len}字符):")
        print(f"  {listing.description}")
        print(f"\n搜索词: {listing.search_terms}")

        problems = validate_listing(listing)
        print(f"\n硬校验: {'通过 ✅' if not problems else problems}")
        print(f"质检: {'合格 PASS ✅' if out['passed'] else '仍不合格（已重写到上限，可人工修改）'}")
        print(f"共生成 {out['revision_count']} 版（不合格自动带意见回炉，上限 3 版）")

def main():
    print(WELCOME)
    while True:
        text = input("\n你: ")
        if text.strip() in ("退出", "exit", "quit", "q"):
            print("再见!")
            break

        # 安全门：疑似注入直接拦掉；再把 PII 打码后才允许往下走
        if detect_injection(text):
            print("⚠️ 检测到疑似 Prompt 注入，已拦截。")
            continue
        text = mask_pii(text)

        intent, keyword, language = parse_intent(text)

        if intent == "unknown":
            print("没听懂,试试: '帮我选品保温杯' 或 '帮我写Listing'")
            continue
        handle(intent, keyword, language)

if __name__ == "__main__":
    main()
