import os
from dotenv import load_dotenv
from dashscope import Generation

# 加载 .env 文件中的环境变量
load_dotenv()
api_key = os.getenv("DASHSCOPE_API_KEY")

if not api_key:
    raise ValueError("未找到 DASHSCOPE_API_KEY，请检查 .env 文件")

def call_qwen(prompt_text):
    """调用通义千问Max模型"""
    response = Generation.call(
        model='qwen-max',
        prompt=prompt_text,
        api_key=api_key
    )
    if response.status_code == 200:
        return response.output.text
    else:
        return f"错误：{response.code} - {response.message}"

if __name__ == "__main__":
    user_prompt = "用一句话介绍深圳的科技创新氛围。"
    result = call_qwen(user_prompt)
print("千问回答：", result)