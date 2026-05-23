import random
from collections.abc import Generator

import pytest

from DiceLang.astnode import AstNode, BinaryOpNode, NumberNode, UnaryOpNode
from DiceLang.error import DiceLangError, EvaluatorError, TodoError
from DiceLang.evaluator import Evaluator
from DiceLang.tokens import TokenType as tktype

RNG = random.Random(42)  # 固定随机种子, 以便复现


# --- 辅助函数 ---
class _Color:
    RED = "\033[91m"
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    BOLD = "\033[1m"
    RESET = "\033[0m"


def eval_or_error(node: AstNode) -> Generator[AstNode] | DiceLangError:
    """求值并捕获错误，总是返回结果供测试打印。"""
    try:
        return Evaluator(rng=RNG).eval(node)
    except DiceLangError as e:
        return e


def eval_final(node: AstNode) -> NumberNode | DiceLangError:
    """求值并返回最终结果（NumberNode），捕获错误。"""
    try:
        result = Evaluator(rng=RNG).eval(node)
        *_, final = result
        return final
    except DiceLangError as e:
        return e


def _log(desc: str, result) -> None:
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
    num1 = NumberNode(value=1)
    plus1_1 = BinaryOpNode(op=tktype.PLUS, left=num1, right=num1)
    plus1_1_1 = BinaryOpNode(op=tktype.PLUS, left=plus1_1, right=num1)
    mult = BinaryOpNode(op=tktype.MULTIPLY, left=plus1_1_1, right=plus1_1)
    expr = BinaryOpNode(op=tktype.PLUS, left=mult, right=plus1_1)

    result = eval_final(expr)
    _log("(1+1+1)*(1+1)+(1+1)", result)
    assert isinstance(result, NumberNode)
    assert result.value == 8


@pytest.mark.parametrize(
    "expr, expected",
    [
        # 加减乘除取模
        ("3 + 4", 7),
        ("10 - 3", 7),
        ("6 * 7", 42),
        ("7 / 2", 3),  # 地板除
        ("7 % 3", 1),
        # 幂运算
        ("2 ^ 3", 8),
        # 嵌套
        ("1 + 2 * 3", 7),
        ("(1 + 2) * 3", 9),
        # 一元运算符
        ("-5", -5),
        ("+3", 3),
        ("-1 + 5", 4),
    ],
)
def test_arithmetic_exprs(expr: str, expected: int):
    """手写 AST 测试各种算术表达式"""
    # 这些用例虽然手写 AST 不方便，但表达式足够简单
    from DiceLang.lexer import Lexer
    from DiceLang.parser import Parser

    ast = Parser(Lexer(expr).tokens).ast
    result = eval_final(ast)
    _log(expr, result)
    assert isinstance(result, NumberNode)
    assert result.value == expected


# ============================================================
# 幂运算右结合
# ============================================================


def test_power_right_associative():
    """2^3^2 = 2^(3^2) = 2^9 = 512"""
    # 手写: 2^(3^2)
    inner = BinaryOpNode(op=tktype.POW, left=NumberNode(value=3), right=NumberNode(value=2))
    expr = BinaryOpNode(op=tktype.POW, left=NumberNode(value=2), right=inner)

    result = eval_final(expr)
    _log("2^3^2", result)
    assert isinstance(result, NumberNode)
    assert result.value == 512


# ============================================================
# 一元运算符
# ============================================================


def test_unary_minus_number():
    node = UnaryOpNode(op=tktype.MINUS, operand=NumberNode(value=42))
    result = eval_final(node)
    _log("-42", result)
    assert isinstance(result, NumberNode)
    assert result.value == -42


def test_unary_plus_number():
    node = UnaryOpNode(op=tktype.PLUS, operand=NumberNode(value=7))
    result = eval_final(node)
    _log("+7", result)
    assert isinstance(result, NumberNode)
    assert result.value == 7


# ============================================================
# Fuzzing 占位
# ============================================================


@pytest.mark.xfail(reason="待实现", strict=True, raises=TodoError)
def test_fuzzing_eval():
    raise TodoError("test_fuzzing_eval")
