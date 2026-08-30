
from graph.state import ReportState
from agents.schemas import DraftReport
from llm import get_llm, call_with_retry
def writer_node(state: ReportState)->dict:
    notes=state["research_notes"]
    feedback=state.get("feedback","")
    if feedback:
        prompt=(
            "你是报告撰写员。请根据资料撰写报告，并针对审核意见修改上一版草稿。\n"
            f"上一版草稿：\n{state['draft']}\n\n"
            f"审核意见：\n{feedback}\n\n"
             "必须逐条回应每条意见，输出修改后的报告。"

                    )
    else:
        prompt=(
            "你是报告撰写员。请根据资料撰写结构完整的技术报告（标题+若干章节+结论）。\n"
            f"资料：\n{notes}"
        )    

    llm=get_llm().with_structured_output(DraftReport)
    result = call_with_retry(llm, prompt)
    report=f"标题：{result.title}\n\n"+"\n\n".join(result.sections)+ f"\n\n结论：{result.conclusion}" 
    return {"draft":report}

if __name__=="__main__":
    state={
        "topic": "AI行业趋势 2026",
        "research_notes": "【关键事实】AI工具生态繁荣，收录1000+工具；Kimi发布K3。\n\n【总结】2026年AI进入工程化阶段。",
        "draft": "",
        "feedback": "",
        "passed": False,
        "final_report": "",
        "revision_count": 0,
    }
    out1=writer_node(state)
    print("===第一次写的草稿===")
    print(out1["draft"][:300])

    state["feedback"]="章节只有标题没有正文，请为每个章节补充具体内容"
    state["draft"]=out1["draft"]
    out2=writer_node(state)
    print("\n===按修改意见重写的草稿===")
    print(out2["draft"])