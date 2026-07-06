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
    #
    user_prompt = """	原则1：写出清晰、具体的指令（指定输出格式、长度、角色）。
	原则2：给模型时间“思考”（要求逐步推理，如“先分析，再转换”）。
	策略：使用示例（few-shot）来引导输出风格。
	策略：明确要求结构化输出（JSON、键值对）。
	姓名：王小明
	学校：南昌理工学院 计算机科学与技术 2026届
	技能：Python, Java, MySQL, Linux, Git
	经历：在江西星澜科技有限公司实习半年职务是AI Agent应用开发实习生，业务：RAG问答智能体基础开发：参与搭建面向业务场景的轻量RAG问答智能体，基于LangChain完成文档切片、向量检索、结果召回等核心环节的基础开发，结合场景需求完成Prompt针对性优化，有效提升复杂问题回答的准确性与相关性。
	AI Agent工具链开发测试：参与梳理AI Agent多工具调用的核心逻辑，基于Function Call交互协议完成3个业务自定义工具的功能开发与验证，整理覆盖全流程的测试用例，将工具调用成功率提升近10%。
	项目支撑与工程协作：依托Pandas、NumPy完成业务结构化/时间序列数据的清洗、预处理等基础工作，配合团队完成模型效果验证并整理实验数据；全程使用Git完成版本管理，配合梳理更新开发文档，借助GitHub Copilot等AI编程工具提升开发效率，适配团队协作开发节奏。
，在校期间做过课程设计——独自完成膳食健康管理系统。
其他：，平时自学AI相关知识，近期在学LangChain。
	
	角色：你是一位资深职业简历优化专家。
	任务：用户会给你一段应届生经历描述，你需要将其改写为STAR法则（情境、任务、行动、结果）格式，并输出纯JSON。
	输出JSON格式：
	{
	  "original": "用户输入原文",
	  "star_version": {
	    "situation": "",
	    "task": "",
	    "action": "",
	    "result": ""
	  },
	  "skills_highlighted": ["提取出的技能"]
	}
	转化要求：
	- 即使原文信息不足，也要合理推断情境和结果，但要确保真实可信。
	- action部分必须使用具体的行为动词如“设计、实现、优化”。
输出必须是纯JSON，前后不要有任何其他文字。
"""
    result = call_qwen(user_prompt)
    print("千问回答：", result)