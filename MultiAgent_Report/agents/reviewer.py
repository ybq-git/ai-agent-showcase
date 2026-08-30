from graph.state import ReportState
from agents.schemas import ReviewResult
from llm import get_llm, call_with_retry 

def reviewer_node(state:ReportState) ->dict:
    draft=state['draft']
    notes = state["research_notes"]


#第一步结构检查（纯代码，不调用llm）
    has_title="标题" in draft
    has_conclusion = "结论" in draft
    if not (has_title and has_conclusion):
        return{
            "passed": False,
            "feedback": "结构不完整：报告缺少标题或结论。",
            "revision_count": state["revision_count"] + 1,
            "final_report": "",
        }

    llm=get_llm().with_structured_output(ReviewResult)
    prompt=(
        "你是报告审核员。请对照研究资料，检查报告草稿中的事实是否与资料一致、有无编造。\n"
        f"研究资料：\n{notes}\n\n"
        f"报告草稿：\n{draft}\n\n"
        "如果事实准确，passed=True；如果发现与资料不符或凭空编造，passed=False。"
        "请同时给出0-100的分数和具体的修改意见。"
    )
    result = call_with_retry(llm, prompt)
    return{
        "passed": result.passed,
        "feedback": result.feedback,
        "revision_count": state["revision_count"] + 1,
        "final_report": draft if result.passed else "",
    }
if __name__=="__main__":
    
    state={
           "topic": "AI行业趋势 2026",
           "research_notes": "【关键事实】AI工具生态繁荣，收录1000+工具；Kimi发布K3。\n\n【总结】2026年AI进入工程化阶段。",
           "draft": "标题：AI趋势报告\n\n内容...\n\n结论：AI进入工程化阶段。",

           "feedback": "",
           "passed": False,
           "final_report": "",
           "revision_count": 0,
       }
    result=reviewer_node(state)
    print(result)