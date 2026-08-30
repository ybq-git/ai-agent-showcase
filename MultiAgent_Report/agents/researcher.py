from graph.state import ReportState
from agents.schemas import ResearchResult
from tools.search import web_search
from llm import get_llm
from llm import get_llm, call_with_retry

def researcher_node(state:ReportState)->dict:
    #第一步：读工单上的主题
    topic=state["topic"]


    #第二步：搜索，拿原始结果文本
    raw=web_search.invoke(topic)

    #第三步：绑定表格模板，让 LLM 把资料整理成结构化数据
    #prompt 里要告诉它：根据搜索结果提炼关键事实和总结
    #并且——如果搜索结果报错或为空，要如实说资料不足，不能编造
    llm=get_llm().with_structured_output(ResearchResult)
    prompt = (
    "你是一名资料研究员。请根据以下搜索结果，提炼关键事实和一句总结。\n"
    f"主题：{topic}\n\n"
    f"搜索结果：\n{raw}\n\n"
    "注意：如果搜索结果是错误信息或为空，请如实说明资料不足，不要编造。"
)
    result = call_with_retry(llm, prompt)




     # 第4步：把结构化数据拼成一段好读的文本，存进工单
    notes="【关键事实】\n"+"\n".join(f"-{f}"for f in result.key_facts)+ "\n\n【总结】" + result.summary
    return{"research_notes":notes}


if __name__ == "__main__":

    state = {                                  # ① 造工单：7 个字段
        "topic": "AI行业 2026 趋势 报告",
        "research_notes": "",
        "draft": "",
        "feedback": "",
        "passed": False,
        "final_report": "",
        "revision_count": 0,
    }
    out = researcher_node(state)               # ② 调函数，传入工单
    print(out["research_notes"])               # ③ 打印返回的资料
