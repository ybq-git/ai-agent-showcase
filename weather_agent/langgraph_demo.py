from typing import TypedDict
from langgraph.graph import StateGraph, END

# 定义状态
class MyState(TypedDict):
    city: str
    weather_info: str
    suggestion: str

# 节点1：模拟获取天气（真实学习中可能返回假数据）
def get_weather(state: MyState):
    # 模拟
    state["weather_info"] = f"{state['city']}今天晴，15-25度"
    return state

# 节点2：生成建议
def give_advice(state: MyState):
    state["suggestion"] = f"根据天气，建议穿薄外套。"
    return state

# 构建图
builder = StateGraph(MyState)
builder.add_node("weather", get_weather)
builder.add_node("advice", give_advice)
builder.set_entry_point("weather")
builder.add_edge("weather", "advice")
builder.add_edge("advice", END)

graph = builder.compile()

# 运行
initial_state = {"city": "深圳", "weather_info": "", "suggestion": ""}
final_state = graph.invoke(initial_state)
print(final_state)
