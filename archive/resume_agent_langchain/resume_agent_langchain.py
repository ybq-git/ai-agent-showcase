"""
使用LangChain重构简历优化Agent，代码更简洁、更健壮
"""
from langchain_core.prompts import ChatPromptTemplate
from langchain_community.chat_models import ChatTongyi
from langchain_core.output_parsers import StrOutputParser
from dotenv import load_dotenv
import os, json

load_dotenv()

llm = ChatTongyi(model="qwen-max", dashscope_api_key=os.getenv("DASHSCOPE_API_KEY"))

# 直接将原来的Prompt改造为LangChain模板
resume_prompt = ChatPromptTemplate.from_template("""
你是一位资深职业简历优化专家。请将以下应届生经历改写为STAR法则格式，输出纯JSON。

输出格式要求：
{{
  "original": "用户输入原文",
  "star_version": {{
    "situation": "情境描述",
    "task": "任务描述",
    "action": "具体行动（用动词）",
    "result": "结果与收获"
  }},
  "skills_highlighted": ["技能1", "技能2"]
}}

注意：输出必须是一个有效的JSON对象，不带任何Markdown代码块标记，不带额外解释。

用户经历：
{user_input}

""")

# 构建链
chain = resume_prompt | llm | StrOutputParser()

def optimize_resume_langchain(experience_text: str) -> dict:
    response = chain.invoke({"user_input": experience_text})
    clean = response.strip().removeprefix("```json").removesuffix("```").strip()
    try:
        return json.loads(clean)
    except:
        return {"error": "解析失败", "raw": response}

if __name__ == "__main__":
    with open("my_resume.txt", "r", encoding="utf-8") as f:
        text = f.read()
    print("原简历：", text)
    result = optimize_resume_langchain(text)
    print(json.dumps(result, ensure_ascii=False, indent=2))