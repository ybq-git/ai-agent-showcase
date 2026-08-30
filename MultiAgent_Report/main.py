from graph.workflow import app

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
    print("=== 最终报告 ===")
    print(result["final_report"])
    print("\n=== 修改次数 ===")
    print(result["revision_count"])

