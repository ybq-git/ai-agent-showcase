from langgraph.graph import StateGraph,START,END
from graph.state import ReportState
from agents.researcher import researcher_node
from agents.writer import writer_node
from agents.reviewer import reviewer_node

#分拣员：根据工单上的信息，说出去下一站去哪
def should_continue(state:ReportState) ->str:
    if state["passed"]:
        return "end"
    if state["revision_count"]>=3:
        return "end"
    return "writer"

graph =StateGraph(ReportState)
graph.add_node("researcher",researcher_node)
graph.add_node("writer",writer_node)
graph.add_node("reviewer",reviewer_node)
graph.add_edge(START,"researcher")
graph.add_edge("researcher","writer")
graph.add_edge("writer","reviewer")
graph.add_conditional_edges("reviewer",should_continue,{"end":END,"writer":"writer"})
app=graph.compile()




if __name__ == "__main__":
    state = {
        "topic": "AI行业未来的发展趋势2026",
        "research_notes": "",
        "draft": "",
        "feedback": "",
        "passed": False,
        "final_report": "",
        "revision_count": 0,
    }
    result = app.invoke(state)
    print("资料字段:", result["research_notes"][:50])   # 研究员跑了吗？
    print("草稿字段:", result["draft"][:50])            # 写作员跑了吗？
    print("最终报告:\n", result["final_report"])
    print("修改次数:", result["revision_count"])