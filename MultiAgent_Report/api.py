from fastapi import FastAPI
from pydantic import BaseModel
from graph.workflow import app as workflow   # 工作流改名 workflow，避开和 FastAPI 的 app 撞名

app = FastAPI()          # FastAPI 应用（菜单）

class ReportRequest(BaseModel):       # 客人送来：一个主题
    topic: str

class ReportResponse(BaseModel):      # 我们端回去：报告 + 修改次数
    report: str
    revision_count: int

@app.post("/report")                  # 口子：POST /report
async def generate_report(req: ReportRequest):   # 异步函数，因为要 await 工作流
    state = {                          # 初始工单状态（照抄 main.py 的写法）
        "topic": req.topic,
        "research_notes": "",
        "draft": "",
        "feedback": "",
        "passed": False,
        "final_report": "",
        "revision_count": 0,
    }
    result = await workflow.ainvoke(state)      # 异步跑整个工作流！
    return ReportResponse(
        report=result["final_report"],          # 从结果里取出最终报告
        revision_count=result["revision_count"],# 取出修改次数
    )
