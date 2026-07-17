from typing import TypedDict, List
from langgraph.graph import StateGraph, END
from resume_analyst_agent import analyze_resume
from resource_recommender_agent import recommend_resources_with_search

class CareerState(TypedDict):
    resume_text: str
    weaknesses: List[str]
    suggestions: str
    resources: List[dict]

def node_analyze(state: CareerState):
    result = analyze_resume(state["resume_text"])
    state["weaknesses"] = result.get("weaknesses", [])
    state["suggestions"] = result.get("suggestions", "")
    return state

def node_recommend(state: CareerState):
    if state["weaknesses"]:
        recs = recommend_resources_with_search({"weaknesses": state["weaknesses"]})
        state["resources"] = recs
    else:
        state["resources"] = []
    return state

builder = StateGraph(CareerState)
builder.add_node("analyze", node_analyze)
builder.add_node("recommend", node_recommend)
builder.set_entry_point("analyze")
builder.add_edge("analyze", "recommend")
builder.add_edge("recommend", END)

career_graph = builder.compile()

if __name__ == "__main__":
    from pathlib import Path
    script_dir = Path(__file__).parent
    with open(script_dir / "my_resume.txt", "r", encoding="utf-8") as f:
        resume_text = f.read()
    init_state = {"resume_text": resume_text, "weaknesses": [], "suggestions": "", "resources": []}
    final = career_graph.invoke(init_state)
    print("弱点：", final["weaknesses"])
    print("建议：", final["suggestions"])
    print("资源：", final["resources"])