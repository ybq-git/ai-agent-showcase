from dotenv import load_dotenv
import os
from openai import OpenAI
load_dotenv()  # 意义：加载.env中的API Key
client = OpenAI(
    api_key=os.getenv("KIMI_API_KEY"),
    base_url="https://api.moonshot.cn/v1",
)
response = client.chat.completions.create(
    model="moonshot-v1-8k",
    messages=[{"role": "user", "content": "介绍下你自己"}],
)
print(response.choices[0].message.content)  # 打印AI回复
