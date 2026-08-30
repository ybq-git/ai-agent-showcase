from langchain_community.chat_models import ChatTongyi
from dotenv import load_dotenv
import os
load_dotenv()

def get_llm():
    llm=ChatTongyi(
        model="qwen-plus",
        base_url=os.getenv("DASHSCOPE_BASE_URL"),
        api_key=os.getenv("DASHSCOPE_API_KEY"),
        temperature=0.1
    )

    return llm
def call_with_retry(llm, prompt, tries=3):
    """调用大模型；万一它返回格式不对、或干脆没按格式输出，就自动重试几次。"""
    last = None
    for i in range(tries):
        try:
            result = llm.invoke(prompt)
            if result is None:                      # ← 新增：模型返回了空，也算失败
                raise ValueError("模型没有返回结构化的结果")
            return result
        except Exception as e:                      # 任何出错都记下，下轮再试
            print(f"⚠️ 第 {i+1} 次调用出错，重试... {str(e)[:60]}")
            last = e
    raise last                                      # 试满 3 次都不行，才彻底抛错
                                 # 重试 3 次都不行，才真的抛错

if __name__=="__main__":
    llm=get_llm()
    resp=llm.invoke("你好，请用一句话介绍你")
    print(resp.content)