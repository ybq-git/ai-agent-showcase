import os, httpx, json
from typing import TypedDict, List
from langgraph.graph import StateGraph, END
from langchain_community.chat_models import ChatTongyi
from langchain_core.messages import HumanMessage, SystemMessage
from dotenv import load_dotenv

load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), "..", ".env"))
llm = ChatTongyi(model="qwen-max", dashscope_api_key=os.getenv("DASHSCOPE_API_KEY"))

class WeatherState(TypedDict):
    city: str
    weather_data: str       # 原始天气JSON字符串
    suggestion: str         # AI穿衣建议
    history: List[str]      # 历史记录

def fetch_weather(state: WeatherState):
    """节点1：调用高德天气API获取实时天气"""
    key = os.getenv("AMAP_KEY")
    city = state["city"]
    url = f"https://restapi.amap.com/v3/weather/weatherInfo?key={key}&city={city}&extensions=base"
    try:
        resp = httpx.get(url, timeout=10.0)
        resp.raise_for_status()
        data = resp.json()
        state["weather_data"] = json.dumps(data, ensure_ascii=False)
    except Exception as e:
        state["weather_data"] = json.dumps({"error": f"天气API调用失败: {e}"}, ensure_ascii=False)
    return state

def generate_suggestion(state: WeatherState):
    """节点2：用千问根据天气数据生成穿扮建议"""
    prompt = f"""
    当前天气数据如下（JSON）：{state['weather_data']}
    请用中文给出简洁的穿衣建议和是否带伞提示。
    """
    ai_msg = llm.invoke([HumanMessage(content=prompt)])
    state["suggestion"] = ai_msg.content
    state["history"].append(f"{state['city']}: {state['suggestion'][:50]}...")
    return state

# 构建图
builder = StateGraph(WeatherState)
builder.add_node("fetch_weather", fetch_weather)
builder.add_node("suggest", generate_suggestion)
builder.set_entry_point("fetch_weather")
builder.add_edge("fetch_weather", "suggest")
builder.add_edge("suggest", END)

agent = builder.compile()

if __name__ == "__main__":
    init_state = {"city": "吉安", "weather_data": "", "suggestion": "", "history": []}
    result = agent.invoke(init_state)
    print("穿衣建议：", result["suggestion"])
    print("历史记录：", result["history"])
