"""日期时间工具

提供当前时间、日期等系统信息
"""

from datetime import datetime
from langchain_core.tools import tool


@tool
def get_current_time(query: str = "") -> str:
    """获取当前日期和时间。参数 query 可选，例如 'date' 仅返回日期，或留空获取完整时间。

    返回当前年月日、时分秒、星期几。
    """
    now = datetime.now()
    weekday_map = ["星期一", "星期二", "星期三", "星期四", "星期五", "星期六", "星期日"]
    return (
        f"当前时间：{now.strftime('%Y年%m月%d日 %H:%M:%S')} "
        f"{weekday_map[now.weekday()]}"
    )
