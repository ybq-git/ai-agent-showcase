"""天气查询工具

使用高德天气 API 查询指定城市的实时天气
"""

import os
import httpx
import json
from langchain_core.tools import tool


@tool
def get_weather(city: str) -> str:
    """查询指定城市的实时天气信息。参数 city 为城市中文名称，例如 '北京'、'深圳'。

    返回天气概况，包括温度、天气状况、风力等。
    """
    key = os.getenv("AMAP_KEY")
    if not key:
        # 尝试从 streamlit secrets 获取
        try:
            import streamlit as st
            key = st.secrets["AMAP_KEY"]
        except Exception:
            pass

    if not key:
        return "错误：未配置高德地图 API Key（AMAP_KEY）"

    url = f"https://restapi.amap.com/v3/weather/weatherInfo?key={key}&city={city}&extensions=base"
    try:
        resp = httpx.get(url, timeout=10.0)
        resp.raise_for_status()
        data = resp.json()

        if data.get("status") == "0":
            return f"查询失败：{data.get('info', '未知错误')}，请检查城市名称是否正确"

        lives = data.get("lives", [])
        if not lives:
            return f"未找到城市 '{city}' 的天气数据"

        live = lives[0]
        return json.dumps({
            "城市": live.get("city"),
            "天气": live.get("weather"),
            "温度": f"{live.get('temperature')}°C",
            "风力": f"{live.get('windpower')}级",
            "湿度": live.get("humidity"),
            "报告时间": live.get("reporttime"),
        }, ensure_ascii=False, indent=2)

    except httpx.TimeoutException:
        return "查询超时，请稍后重试"
    except Exception as e:
        return f"天气查询出错：{e}"
