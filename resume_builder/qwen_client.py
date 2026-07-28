import os
from dotenv import load_dotenv
from dashscope import Generation

load_dotenv()
api_key = os.getenv("DASHSCOPE_API_KEY")

if not api_key:
    raise ValueError("未找到 DASHSCOPE_API_KEY，请检查 .env 文件")


def call_qwen(prompt_text: str) -> str:
    """调用通义千问Max模型"""
    response = Generation.call(
        model="qwen-max",
        prompt=prompt_text,
        api_key=api_key,
    )
    if response.status_code == 200:
        return response.output.text
    else:
        raise RuntimeError(f"千问API错误：{response.code} - {response.message}")
