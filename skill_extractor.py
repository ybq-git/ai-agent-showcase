"""
技能提取工具：输入一段自我介绍，调用千问提取技能关键词，返回JSON格式列表。
"""
import json
import time
import re
from test_qwen import call_qwen  # 复用之前的调用函数


def extract_skills_from_bio(bio_text, max_retries=3):
    """从自我介绍文本中提取技术技能和软技能，返回字典。"""
    # 构造提示词，要求模型以 JSON 格式返回两类技能
    prompt = (
        "请从下面的自我介绍中提取技能关键词，"
        "并以如下 JSON 格式返回（不要包含任何额外说明）：\n"
        '{"technical_skills": ["技能1", "技能2"], "soft_skills": ["技能1", "技能2"]}\n\n'
        f"自我介绍：{bio_text}"
    )

    for attempt in range(max_retries):
        response = call_qwen(prompt)
        try:
            # 先尝试直接解析整个返回内容为 JSON
            skills = json.loads(response)
            return skills
        except json.JSONDecodeError:
            # 可能返回的文本中混有 JSON，尝试抽取花括号内容
            match = re.search(r'\{.*\}', response, re.DOTALL)
            if match:
                try:
                    skills = json.loads(match.group(0))
                    return skills
                except json.JSONDecodeError:
                    pass
            if attempt < max_retries - 1:
                time.sleep(1)  # 避免 API 限流，等待后重试

    # 多次重试后仍无法解析，返回空结构
    return {"technical_skills": [], "soft_skills": []}


if __name__ == "__main__":
    test_bio = (
        "我是计算机专业应届生，会Python和Java，使用过MySQL、Linux系统，有良好的自学能力和沟通能力。"
    )
    print("原始自我介绍：", test_bio)
    skills_dict = extract_skills_from_bio(test_bio)
    print("千问提取结果：", skills_dict)
    print("技术技能：", skills_dict.get("technical_skills"))
    print("软技能：", skills_dict.get("soft_skills"))
