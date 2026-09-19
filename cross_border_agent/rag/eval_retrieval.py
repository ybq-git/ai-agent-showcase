"""用人工标注的测试集，算检索的 MRR。

用例设计原则：用"卖家会怎么问"的口语化措辞，而不是照抄文档原文。
照抄原文的用例只测关键词匹配，测不出语义检索的真实能力。
"""
import sys
import os
import collections

sys.stdout.reconfigure(encoding='utf-8')
# 允许直接 `python rag/eval_retrieval.py` 运行
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from rag.hybrid import hybrid_search

TITLE = "亚马逊商品标题规范.txt"
BULLETS = "亚马逊五点描述(Bullet Points)规范.txt"
COMPLIANCE = "亚马逊禁售与合规.txt"
IMAGE = "亚马逊商品图片规范.txt"
APLUS = "亚马逊A+页面规范.txt"
VARIATION = "亚马逊变体合并规则.txt"
FBA = "亚马逊FBA入仓与包装要求.txt"
PERF = "亚马逊账户绩效指标.txt"
ADS = "亚马逊广告投放规范.txt"
CATEGORY = "亚马逊商品分类与类目审核.txt"
RETURN = "亚马逊退货与售后政策.txt"
BRAND = "亚马逊品牌注册与品牌保护.txt"
IP = "亚马逊知识产权投诉与申诉.txt"
REVIEW = "亚马逊商品评论政策.txt"
PRICING = "亚马逊定价与促销规则.txt"

# 测试集：(问题, 期望命中的来源文档)。共 57 条，覆盖全部 15 份文档。
TEST_CASES = [
    # ---------- 标题规范（11 条）----------
    ("商品标题最多能写多少个字", TITLE),
    ("珠宝类目的标题可以写长一点吗", TITLE),
    ("一个合格的标题需要包含哪些信息", TITLE),
    ("标题能不能全部用大写字母", TITLE),
    ("标题里带 © 或者 ® 这种符号会不会违规", TITLE),
    ("标题里介词需要大写吗", TITLE),
    ("标题中的数字要写成英文单词吗", TITLE),
    ("标题写“最棒的保温杯”可以吗", TITLE),
    ("我的商品被提示标题含特殊字符，是哪些字符", TITLE),
    ("品牌名和材质这些要写进标题里吗", TITLE),
    ("标题里写“限时特价”会被判违规吗", TITLE),

    # ---------- 五点描述规范（11 条）----------
    ("五点描述最多能写几条", BULLETS),
    ("每一条卖点有字数上限吗", BULLETS),
    ("每条卖点的开头要写什么", BULLETS),
    ("“DURABLE:”这种格式是必须的吗", BULLETS),
    ("卖点里能写价格或者打折信息吗", BULLETS),
    ("卖点描述里可以放客服邮箱吗", BULLETS),
    ("卖点里能写发货时效吗", BULLETS),
    ("卖点用“the best”这种说法行不行", BULLETS),
    ("卖点内容应该围绕什么来写", BULLETS),
    ("卖点里可以包含保修信息吗", BULLETS),
    ("卖点里要不要写清楚材质和尺寸", BULLETS),

    # ---------- 禁售与合规（11 条）----------
    ("卖没拿到授权的品牌货会有什么后果", COMPLIANCE),
    ("水杯内胆这种接触食物的材料有什么要求", COMPLIANCE),
    ("FDA 检测报告需要保留吗", COMPLIANCE),
    ("带电池的商品怎么才能正常入仓", COMPLIANCE),
    ("UN38.3 是针对什么产品的要求", COMPLIANCE),
    ("易燃液体这类商品能直接上架卖吗", COMPLIANCE),
    ("危险品审核的流程是什么", COMPLIANCE),
    ("普通家居用品能宣传杀菌功能吗", COMPLIANCE),
    ("商品描述里写“医用级”需要什么资质", COMPLIANCE),
    ("假货被平台查到了会怎么样", COMPLIANCE),
    ("食品接触类材料有什么合规要求", COMPLIANCE),

    # ---------- 图片规范（2 条）----------
    ("主图的背景色有什么要求", IMAGE),
    ("商品在图片里需要占多大比例", IMAGE),

    # ---------- A+ 页面（2 条）----------
    ("做 A+ 页面需要什么前提条件", APLUS),
    ("A+ 页面里能写促销信息吗", APLUS),

    # ---------- 变体合并（2 条）----------
    ("不同颜色的同款商品能合并成一个链接吗", VARIATION),
    ("把新链接挂到老链接下面继承评论行不行", VARIATION),

    # ---------- FBA 入仓（2 条）----------
    ("发到 FBA 的箱子最重能装多少", FBA),
    ("外箱尺寸超过标准了怎么处理", FBA),

    # ---------- 账户绩效（2 条）----------
    ("订单缺陷率要控制在多少以内", PERF),
    ("买家发来的消息多久必须回复", PERF),

    # ---------- 广告投放（2 条）----------
    ("广告文案里能写打折吗", ADS),
    ("投竞品的 ASIN 有什么限制", ADS),

    # ---------- 商品分类（2 条）----------
    ("哪些类目需要先通过审核才能卖", CATEGORY),
    ("商品放错类目会有什么影响", CATEGORY),

    # ---------- 退货售后（2 条）----------
    ("买家收到货后多久之内可以退货", RETURN),
    ("收到退货请求要多久内处理", RETURN),

    # ---------- 品牌注册（2 条）----------
    ("申请品牌注册需要什么条件", BRAND),
    ("品牌旗舰店最少要几个产品才能搭", BRAND),

    # ---------- 知识产权（2 条）----------
    ("被投诉侵权了多久之内必须申诉", IP),
    ("申诉要提供什么材料才有效", IP),

    # ---------- 评论政策（2 条）----------
    ("包装盒里能放索评卡片吗", REVIEW),
    ("Vine 计划一个产品能有多少个评论名额", REVIEW),

    # ---------- 定价促销（2 条）----------
    ("划线价可以随便写吗", PRICING),
    ("秒杀一般要求打几折", PRICING),
]


def reciprocal_rank(hits, expected_source):
    """看期望文档排第几：第1名→1，第3名→1/3，没排进→0。"""
    for rank, hit in enumerate(hits, start=1):
        if hit["source"] == expected_source:
            return 1.0 / rank
    return 0.0


def eval_mrr(top_k: int = 5, verbose: bool = False) -> float:
    total = 0.0
    per_source = collections.defaultdict(lambda: [0, 0])   # source -> [命中数, 总数]
    per_source_mrr = collections.defaultdict(float)

    for query, expected in TEST_CASES:
        hits = hybrid_search(query, top_k=top_k)["context"]
        rr = reciprocal_rank(hits, expected)
        total += rr
        per_source[expected][1] += 1
        per_source_mrr[expected] += rr
        if rr > 0:
            per_source[expected][0] += 1
        if verbose:
            got = [h["source"] for h in hits[:3]]
            print(f"  {'OK ' if rr > 0 else 'MISS'} RR={rr:.3f}  Q: {query}")
            print(f"       期望 {expected} | 实际前3 {got}")

    mrr = total / len(TEST_CASES)
    print(f"\nMRR = {mrr:.3f}  (用例 {len(TEST_CASES)} 条, top_k={top_k})")
    print("\n按来源拆分:")
    for src, (hit, n) in sorted(per_source.items()):
        print(f"  {src}: 命中 {hit}/{n}, 该类 MRR={per_source_mrr[src]/n:.3f}")
    return mrr


if __name__ == "__main__":
    verbose = "-v" in sys.argv
    mrr = eval_mrr(verbose=verbose)
    # 自检：MRR 必须落在 [0,1]，且 33 条用例全部参与计算
    assert 0.0 <= mrr <= 1.0, f"MRR 越界: {mrr}"
    assert len(TEST_CASES) >= 30, f"用例数不足 30 条: {len(TEST_CASES)}"
    print(f"\n自检通过：{len(TEST_CASES)} 条用例，MRR 在合法区间。")
