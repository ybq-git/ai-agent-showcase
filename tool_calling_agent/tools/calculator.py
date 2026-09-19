"""安全计算器工具

使用 eval 的安全替代方案执行数学表达式
"""

import ast
import math
import operator
from langchain_core.tools import tool

# 白名单——只允许安全操作
_ALLOWED_OPS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.Pow: operator.pow,
    ast.USub: operator.neg,
    ast.UAdd: operator.pos,
    ast.Mod: operator.mod,
}

_ALLOWED_FUNCTIONS = {
    "abs": abs,
    "round": round,
    "max": max,
    "min": min,
    "int": int,
    "float": float,
}

# 防资源耗尽：白名单挡得住 RCE，挡不住 9**9**9 这种把 CPU/内存跑满的表达式
_MAX_EXPONENT = 1000       # 幂运算的指数上限
_MAX_BITS = 10_000         # 任意中间结果的位宽上限


def _safe_eval(expr: str) -> float:
    """安全地计算数学表达式，拒绝任何非数学操作"""
    expr = expr.strip()
    tree = ast.parse(expr, mode="eval")

    def _eval(node):
        if isinstance(node, ast.Expression):
            return _eval(node.body)
        elif isinstance(node, ast.Constant):
            return node.value
        elif isinstance(node, ast.BinOp):
            op = _ALLOWED_OPS.get(type(node.op))
            if op is None:
                raise ValueError(f"不支持的操作符：{type(node.op).__name__}")
            left, right = _eval(node.left), _eval(node.right)
            # 幂运算必须先卡指数：等算完再检查就晚了（9**9**9 会先跑满 CPU）
            if isinstance(node.op, ast.Pow) and abs(right) > _MAX_EXPONENT:
                raise ValueError(f"指数过大（上限 {_MAX_EXPONENT}）")
            value = op(left, right)
            # 卡住中间结果位宽，防嵌套放大撑爆内存
            if isinstance(value, int) and value.bit_length() > _MAX_BITS:
                raise ValueError("结果数值过大，已拒绝计算")
            return value
        elif isinstance(node, ast.UnaryOp):
            op = _ALLOWED_OPS.get(type(node.op))
            if op is None:
                raise ValueError(f"不支持的一元操作符：{type(node.op).__name__}")
            return op(_eval(node.operand))
        elif isinstance(node, ast.Call):
            func_name = node.func.id if isinstance(node.func, ast.Name) else str(node.func)
            if func_name not in _ALLOWED_FUNCTIONS:
                raise ValueError(f"不允许的函数调用：{func_name}")
            args = [_eval(a) for a in node.args]
            return _ALLOWED_FUNCTIONS[func_name](*args)
        else:
            raise ValueError(f"不支持的表达式类型：{type(node).__name__}")

    return _eval(tree)


@tool
def calculator(expression: str) -> str:
    """安全地计算数学表达式。

    参数 expression 为数学表达式字符串，支持 +、-、*、/、**（幂）、%（取模）、括号，
    以及 abs、round、max、min、int、float 函数。

    示例：'12345 * 67890'、'(100 + 200) / 3'、'abs(-42)'
    """
    try:
        result = _safe_eval(expression)
    except ZeroDivisionError:
        return "错误：除数不能为零"
    except OverflowError:
        return "错误：数值超出可计算范围"
    except (ValueError, SyntaxError) as e:
        return f"表达式错误：{e}"

    if isinstance(result, float):
        if not math.isfinite(result):          # 1e400 / 1e308*10 会溢出成 inf
            return "错误：数值超出可计算范围"
        if result == int(result):              # 整数显示整数
            result = int(result)
    return f"计算结果：{result}"


if __name__ == "__main__":
    # 自检：正常表达式要能算，恶意表达式要被挡住
    def run(expr):
        return calculator.invoke({"expression": expr})

    assert run("8 * 8") == "计算结果：64"
    assert run("(100 + 200) / 3") == "计算结果：100"     # 整数值的浮点显示成整数
    assert run("10 / 4") == "计算结果：2.5"
    assert "除数不能为零" in run("1 / 0")

    # 溢出：改之前这里会抛 OverflowError 逃出工具，把整个 Agent 中断掉
    assert "超出可计算范围" in run("1e400")
    assert "超出可计算范围" in run("1e308 * 10")

    # 超大幂：改之前 9**9**9 要跑几分钟、吃几百 MB 内存
    assert "指数过大" in run("9**9**9")
    assert "过大" in run("(10**1000)**1000")     # 嵌套放大被位宽卡住

    # RCE 依然被白名单挡住
    assert not run("__import__('os').system('echo hi')").startswith("计算结果")

    print("calculator 自检通过 ✅")
