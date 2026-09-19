import re



#检测"试图覆盖指令"的注入模式
INJECTION_PATTERNS =[
    r"忽略(你)?(上面|之前|以下)?的?(所有)?(指令|命令|规则|提示)",   # "忽略所有指令"
    r"ignore\s+(all\s+)?(previous|prior|above)?\s*(instructions|prompts|rules|commands)",  # "ignore all previous instructions"
    r"你是\s*(一个)?\s*(自由|不受限|没有限制)",                        # "你现在是自由的"
    r"disregard\s+(all\s+)?(previous|prior)?\s*(instructions|rules)",  # "disregard previous rules"
]


def detect_injection(text: str) -> bool:
    """命中任一注入模式 => True(有风险)。fail-closed:宁可错杀。"""
    for pattern in INJECTION_PATTERNS:
        if re.search(pattern, text, re.IGNORECASE):   # IGNORECASE = 不区分大小写
            return True
    return False

PII_PATTERNS = {
    "卡号": r"\b(?:\d[ -]*?){13,16}\b",       # 13-16 位数字(信用卡)
    "手机号": r"1[3-9]\d{9}",                  # 大陆手机号 13800138000
    "身份证": r"\b\d{17}[\dXx]\b",             # 18 位身份证
}

def mask_pii(text: str) -> str:
    """把卡号/手机号/身份证打码。"""
    for name, pattern in PII_PATTERNS.items():
        text = re.sub(pattern, "[已脱敏]", text)   # 替换成占位符
    return text


