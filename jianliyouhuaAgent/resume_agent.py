"""
简历优化Agent：接收用户简单经历，输出STAR法则版简历片段（JSON）
"""
import json
from pathlib import Path

from test_qwen import call_qwen

# 脚本所在目录，作为项目根目录（不依赖当前工作目录）
BASE_DIR = Path(__file__).parent

# 提示词模板（从设计文件中提取并固定）
RESUME_PROMPT_TEMPLATE = """
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
"""

def optimize_resume(experience_text: str) -> dict:
    prompt = RESUME_PROMPT_TEMPLATE.replace("{user_input}", experience_text)
    response = call_qwen(prompt)
    # 容错处理：尝试解析JSON，清洗可能的```json混乱
    clean_response = response.strip()
    if clean_response.startswith("```json"):
        clean_response = clean_response[7:]
    if clean_response.endswith("```"):
        clean_response = clean_response[:-3]
    clean_response = clean_response.strip()
    try:
        return json.loads(clean_response)
    except json.JSONDecodeError:
        # 如果失败，返回原始回复以便调试
        return {"error": "JSON解析失败", "raw": response}

if __name__ == "__main__":
    # 读取本地简历草稿文件（始终相对脚本所在目录）
    resume_path = BASE_DIR / "my_resume.txt"
    with open(resume_path, "r", encoding="utf-8") as f:
        raw_text = f.read()

    print("原简历内容：\n", raw_text)
    print("\n======== 优化中 ========")
    result = optimize_resume(raw_text)

    if "error" in result:
        print(result["error"])
        print(result.get("raw"))
    else:
        print(json.dumps(result, ensure_ascii=False, indent=2))
        # 可以进一步保存到文件
        output_path = BASE_DIR / "resume_optimized.json"
        with open(output_path, "w", encoding="utf-8") as out:
            json.dump(result, out, ensure_ascii=False, indent=2)
        print("\n优化结果已保存到 resume_optimized.json")