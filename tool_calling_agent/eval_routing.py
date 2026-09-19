"""工具路由评估：测 Agent 有没有在正确的场景调用正确的工具。

这是"工具调用成功率"的出处。跑真实模型，逐条问，看它调了哪个工具。

用法：
    python eval_routing.py          # 跑全部用例，输出成功率
    python eval_routing.py -v       # 额外打印每条的实际调用链

注意：本脚本会真实调用 LLM，产生 API 费用（20 条约几分钱）。
"""
import sys
import collections

sys.stdout.reconfigure(encoding='utf-8')

from agent import agent


# (用户问题, 期望调用的工具名；None = 不该调用任何工具)
TEST_CASES = [
    # ---------- 天气（5 条）----------
    ("北京今天天气怎么样", "get_weather"),
    ("深圳现在多少度", "get_weather"),
    ("上海明天会下雨吗", "get_weather"),
    ("杭州冷不冷", "get_weather"),
    ("广州的天气如何", "get_weather"),

    # ---------- 计算（5 条）----------
    ("帮我算一下 123 + 456 等于多少", "calculator"),
    ("计算 (12 * 34) + 56", "calculator"),
    ("100 除以 7 是多少", "calculator"),
    ("2 的 10 次方等于多少", "calculator"),
    ("365 乘以 24 是多少", "calculator"),

    # ---------- 联网搜索（3 条）----------
    ("最近有什么 AI 新闻", "web_search"),
    ("帮我搜一下最新的显卡型号", "web_search"),
    ("2026 年世界杯在哪里举办", "web_search"),

    # ---------- 时间（4 条）----------
    ("现在几点了", "get_current_time"),
    ("今天几号", "get_current_time"),
    ("今天是星期几", "get_current_time"),
    ("当前时间是多少", "get_current_time"),

    # ---------- 不该调工具（3 条）----------
    ("你好", None),
    ("你是谁", None),
    ("谢谢", None),
]

TOOL_NAMES = {"get_weather", "calculator", "web_search", "get_current_time"}


def called_tools(query: str) -> list[str]:
    """跑一次 Agent，返回这次实际被调用的工具名列表（可能多次调用）。"""
    result = agent.invoke({"messages": [{"role": "user", "content": query}]})
    names = []
    for msg in result.get("messages", []):
        for tc in (getattr(msg, "tool_calls", None) or []):
            name = tc.get("name") if isinstance(tc, dict) else getattr(tc, "name", None)
            if name:
                names.append(name)
    return names


# 网络/基础设施异常，不代表 Agent 选错了工具，必须和"选错"分开统计
NETWORK_ERRORS = (ConnectionError, TimeoutError, OSError)


def main(verbose: bool = False) -> tuple[float, float]:
    """返回 (路由正确率, 用例完成率)。

    路由正确率 = 选中正确工具的条数 / 实际执行完成的条数（不含网络异常中断的）。
    用例完成率 = 实际执行完成的条数 / 全部用例数。
    """
    executed = ok = 0
    errored = []
    per_tool = collections.defaultdict(lambda: [0, 0])
    misses = []

    for query, expected in TEST_CASES:
        try:
            actual = called_tools(query)
        except NETWORK_ERRORS as e:
            # 网络挂了，这条没跑成 —— 不计入正确率分母，单独记账
            errored.append((query, type(e).__name__))
            if verbose:
                print(f"  SKIP 网络异常 {type(e).__name__}  Q: {query}")
            continue
        except Exception as e:
            actual = [f"<异常: {type(e).__name__}>"]

        executed += 1
        if expected is None:
            hit = not [n for n in actual if n in TOOL_NAMES]      # 不该调就不调
            label = "无工具"
        else:
            hit = expected in actual
            label = expected
            per_tool[expected][1] += 1
            if hit:
                per_tool[expected][0] += 1

        ok += 1 if hit else 0
        if not hit:
            misses.append((query, label, actual))
        if verbose:
            print(f"  {'OK  ' if hit else 'MISS'} 期望={label:<16} 实际={actual}  Q: {query}")

    route_rate = ok / executed if executed else 0.0
    done_rate = executed / len(TEST_CASES)

    print(f"\n路由正确率 = {ok}/{executed} = {route_rate:.1%}   （只统计实际跑完的）")
    print(f"用例完成率 = {executed}/{len(TEST_CASES)} = {done_rate:.1%}   （差额为网络异常中断）")
    print("\n按工具拆分:")
    for tool, (h, n) in sorted(per_tool.items()):
        print(f"  {tool:<18}: {h}/{n}")

    if misses:
        print("\n选错工具明细:")
        for query, expected, actual in misses:
            print(f"  期望 {expected:<16} 实际 {actual}  Q: {query}")
    if errored:
        print("\n网络异常中断（未计入正确率）:")
        for query, err in errored:
            print(f"  {err:<16} Q: {query}")

    return route_rate, done_rate


if __name__ == "__main__":
    route_rate, done_rate = main(verbose="-v" in sys.argv)
    assert 0.0 <= route_rate <= 1.0, f"路由正确率越界: {route_rate}"
    assert len(TEST_CASES) == 20, f"用例数应为 20，实际 {len(TEST_CASES)}"
    print(f"\n自检通过：{len(TEST_CASES)} 条用例，指标在合法区间。")
