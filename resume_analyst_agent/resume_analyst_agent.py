"""
简历分析Agent节点：接收简历文本，输出弱点和改进建议。
"""
from langchain_community.chat_models import ChatTongyi
from langchain_core.messages import HumanMessage
import os, json
from dotenv import load_dotenv

load_dotenv()
llm = ChatTongyi(model="qwen-max", dashscope_api_key=os.getenv("DASHSCOPE_API_KEY"))

def analyze_resume(resume_text: str) -> dict:
    prompt = f"""
    你是一位职业顾问。请分析以下应届生简历内容，指出3个主要弱点，并给出改进方向。
    输出JSON格式：{{"weaknesses": ["弱点1", "弱点2", "弱点3"], "suggestions": "总体建议"}}
    简历：{resume_text}
    """
    response = llm.invoke([HumanMessage(content=prompt)])
    content = response.content.strip()
    # ponytail: strip markdown code fences
    if content.startswith("```"):
        content = content.split("\n", 1)[-1].rsplit("\n```", 1)[0] if "\n```" in content else content[3:-3]
    try:
        return json.loads(content)
    except:
        return {"weaknesses": [], "suggestions": response.content}

if __name__ == "__main__":
    from pathlib import Path
    script_dir = Path(__file__).parent
    with open(script_dir / "my_resume.txt", "r", encoding="utf-8") as f:
        text = f.read()
    result = analyze_resume(text)
    print(json.dumps(result, ensure_ascii=False, indent=2))
