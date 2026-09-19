from typing import TypedDict
from langgraph.graph import StateGraph, START, END
from modules.listing_generator import generate_listing
from modules.quality import review_listing
from modules.product_research import research_category
class AgentState(TypedDict):
    intent: str
    category: str
    scores: list          # 选品调研结果（ProductScore 列表）
    language: str         # 输出语言："中文" / "英文"
    hero: object          # 主推款（ProductListing）
    listing: object       # 当前版 Listing
    feedback: str         # 最近一次质检反馈
    revision_count: int
    passed: bool


def node_research(state: AgentState) -> dict:
    """选品专家：调研品类 → 打分排序 → 只留过门槛的推荐。"""
    scores = research_category(state["category"], limit=4)
    return {"scores": scores}



MAX_REVISIONS = 3
def node_generate(state:AgentState) ->dict:
    """生成Listing(带上次质检反馈)"""
    listing = generate_listing(
        state["hero"],
        feedback=state.get("feedback", ""),
        language=state.get("language") or "中文",
    )
    return {"listing":listing,"revision_count":state["revision_count"]+1}
def node_review(state:AgentState) ->dict:
        """质检：两层判定。"""
        verdict=review_listing(state["listing"],state["hero"])
        return {
        "passed":verdict.passed,
        "feedback": verdict.llm_feedback + "\n" + "\n".join(verdict.suggestions)

    }

def route_after_review(state: AgentState) -> str:
    """质检后路由：合格或超次数 → 结束；否则回炉。"""
    if state["passed"] or state["revision_count"] >= MAX_REVISIONS:
        return "end"
    return "generate"     # 打回重写
def route(state: AgentState) -> str:
    """白名单路由：只认两个意图，其余默认选品。"""
    if state["intent"] == "listing":
        return "generate"
    return "research"
builder = StateGraph(AgentState)
builder.add_node("research", node_research)      # 保留占位
builder.add_node("generate", node_generate)
builder.add_node("review", node_review)
# research 和 generate 两条入口都进 listing 工作流——这里先简化：listing 意图直接进 generate
builder.add_conditional_edges(START, route)   # route 直接返回节点名，无需映射表
builder.add_edge("research", END)                # research 分支先占位
builder.add_edge("generate", "review")
builder.add_conditional_edges("review", route_after_review, {"generate": "generate", "end": END})
workflow = builder.compile()
