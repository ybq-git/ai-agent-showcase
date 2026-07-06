from langchain_core.prompts import ChatPromptTemplate
from langchain_community.chat_models import ChatTongyi
from langchain_core.output_parsers import StrOutputParser
import os
from dotenv import load_dotenv

load_dotenv()

# 初始化通义千问聊天模型
llm = ChatTongyi(model="qwen-max", dashscope_api_key=os.getenv("DASHSCOPE_API_KEY"))

# 创建提示模板
translation_template = ChatPromptTemplate.from_template(
    "把下面的文本翻译成{target_language}：{text}"
)

# 构建Chain： prompt -> llm -> 字符串输出
chain = translation_template | llm | StrOutputParser()

result = chain.invoke({"target_language": "英文", "text": "人工智能正在改变世界"})
print(result)# 应输出英文翻译