from typing import TypedDict
class ReportState(TypedDict):
    topic	        :str	
    research_notes	:str
    draft	        :str	
    feedback	    :str	
    passed	        :bool	
    final_report	:str	
    revision_count  :int	

if __name__ == "__main__":
    s: ReportState = {          # 冒号：声明 s 的类型是 ReportState
        "topic": "2026年AI行业趋势",
         "research_notes"	:"111",
            "draft"        :"222",	
            "feedback"	    :"333",	
           "passed"	        :True,	
           "final_report"	:"444",
            "revision_count"  : 1234	                # 其余字段给初始值：字符串给 ""，布尔给 False，数字给 0
    }
    print(s)
    print(s.keys())     # 打印所有键，看看有没有多出来的空格/Tab
