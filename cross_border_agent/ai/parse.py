import json
import re
def parse_llm_json(text:str) ->dict:
    """
    从文本中提取 JSON 字符串并解析为字典。
    如果文本中没有有效的 JSON 字符串，则返回空字典。
    """
    # 使用正则表达式匹配 JSON 对象
    text= text.strip()
    
    fence = re.search(r"```(?:json)?\s*(.*?)```", text, re.DOTALL)
    
    if fence:
        text = fence.group(1).strip()
    try:
        result=json.loads(text)
    except json.JSONDecodeError:

        m=re.search(r"\{.*\}",text,re.DOTALL)
        if not m:
            raise ValueError(f"LLM输出里没有 JSON:{text[:100]}")
        result= json.loads(m.group())

    if not isinstance(result,dict):
        raise ValueError(f"期望 dict,但拿到{type(result).__name__}")
    return result

            
