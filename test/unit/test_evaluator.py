import random

import pytest

from DiceLang.astnode import AstNode, BinaryOpNode, NumberNode
from DiceLang.error import DiceLangError, TodoError
from DiceLang.evaluator import Evaluator
from DiceLang.result import EvalResult
from DiceLang.tokens import TokenType as tktype

RNG = random.Random(42)  # 固定随机种子, 以便复现


# --- 辅助函数 ---
class _Color:
    RED = "\033[91m"
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    BOLD = "\033[1m"
    RESET = "\033[0m"


def eval_or_error(node: AstNode) -> EvalResult | DiceLangError:
    """求值并捕获错误，总是返回结果供测试打印。"""
    try:
        return Evaluator(rng=RNG).eval(node)
    except DiceLangError as e:
        return e


def _log(desc: str, result: EvalResult | DiceLangError) -> None:
    is_err = isinstance(result, DiceLangError)
    tag = f"{_Color.RED}{_Color.BOLD}Error{_Color.RESET}" if is_err else f"{_Color.GREEN}OK{_Color.RESET}"
    raw = f"{_Color.YELLOW}{result}{_Color.RESET}" if is_err else str(result)
    indented = raw.replace("\n", "\n  ")
    print(f"\n  case={desc!r}  [{tag}]\n  {indented}")


# ============================================================
# 算术表达式
# ============================================================


def test_arithmetic_complex():
    """测试算术表达式 (1+1+1)*(1+1)+(1+1) = 8"""
    # 构建表达式: (1+1+1)*(1+1)+(1+1)
    num1 = NumberNode(1)
    plus1_1 = BinaryOpNode(tktype.PLUS, num1, num1)          # 1+1 = 2
    plus1_1_1 = BinaryOpNode(tktype.PLUS, plus1_1, num1)     # (1+1)+1 = 3
    mult = BinaryOpNode(tktype.MULTIPLY, plus1_1_1, plus1_1) # 3*2 = 6
    expr = BinaryOpNode(tktype.PLUS, mult, plus1_1)          # 6+2 = 8

    result = eval_or_error(expr)
    _log("(1+1+1)*(1+1)+(1+1)", result)
    # TODO: assert isinstance(result, EvalResult)
    # TODO: assert result.value == 8
    raise TodoError("验证求值结果")


# ============================================================
# Fuzzing 占位
# ============================================================


@pytest.mark.xfail(reason="待实现", strict=True)
def test_fuzzing_eval():
    raise TodoError("test_fuzzing_eval")
