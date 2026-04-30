import pytest

from DiceLang.astnode import (
    AstNode,
    BinaryOpNode,
    DiceNode,
    GroupNode,
    NumberNode,
    UnaryOpNode,
)
from DiceLang.error import DiceLangError, ParserError, TodoError
from DiceLang.lexer import Lexer
from DiceLang.parser import Parser
from DiceLang.tokens import TokenType


# --- 辅助函数 ---
class _Color:
    RED = "\033[91m"
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    BOLD = "\033[1m"
    RESET = "\033[0m"


def parse(source: str) -> AstNode:
    return Parser(Lexer(source).tokens).ast


def parse_or_error(source: str) -> AstNode | DiceLangError:
    """解析并捕获错误，总是返回结果供测试打印。"""
    try:
        return parse(source)
    except DiceLangError as e:
        return e


def _log(source: str, result: AstNode | DiceLangError) -> None:
    is_err = isinstance(result, DiceLangError)
    tag = f"{_Color.RED}{_Color.BOLD}Error{_Color.RESET}" if is_err else f"{_Color.GREEN}OK{_Color.RESET}"
    raw = f"{_Color.YELLOW}{result}{_Color.RESET}" if is_err else str(result)
    indented = raw.replace("\n", "\n  ")
    print(f"\n  case={source!r}  [{tag}]\n  {indented}")


# ============================================================
# 括号与分组
# ============================================================


def test_group_single():
    result = parse_or_error("(1)")
    _log("(1)", result)
    assert isinstance(result, GroupNode)
    assert len(result.group) == 1
    assert isinstance(result.group[0], NumberNode)
    assert result.group[0].value == 1


def test_group_nested():
    result = parse_or_error("((1))")
    _log("((1))", result)
    assert isinstance(result, GroupNode)
    assert len(result.group) == 1
    inner = result.group[0]
    assert isinstance(inner, GroupNode)
    assert isinstance(inner.group[0], NumberNode)
    assert inner.group[0].value == 1


def test_group_binop():
    result = parse_or_error("((1)+(2))")
    _log("((1)+(2))", result)
    assert isinstance(result, GroupNode)
    expr = result.group[0]
    assert isinstance(expr, BinaryOpNode)
    assert expr.op == TokenType.PLUS
    assert isinstance(expr.left, GroupNode)
    assert isinstance(expr.right, GroupNode)


@pytest.mark.parametrize(
    "source",
    [
        "()",
        "((1)",
        "(1))",
        "(1)+)",
        "(1)+(",
        "(1)(2)",
        "((1)(2))",
        "(1()2)",
        "(1+()2)",
        "((1)+2",
        "1+(2))",
        "(1)+(2))",
        "(1+(2)3)",
        "(1+2)3",
        "(1+(2*3)",
    ],
)
def test_group_error(source):
    result = parse_or_error(source)
    _log(source, result)
    assert isinstance(result, ParserError), f"期望 ParserError，得到 {type(result).__name__}: {result}"


# ============================================================
# 基本算术
# ============================================================


def test_addition():
    result = parse_or_error("1+2")
    _log("1+2", result)
    assert isinstance(result, BinaryOpNode)
    assert result.op == TokenType.PLUS
    assert isinstance(result.left, NumberNode) and result.left.value == 1
    assert isinstance(result.right, NumberNode) and result.right.value == 2


def test_multiplication_higher_precedence():
    result = parse_or_error("1+2*3")
    _log("1+2*3", result)
    assert isinstance(result, BinaryOpNode)
    assert result.op == TokenType.PLUS
    assert isinstance(result.left, NumberNode) and result.left.value == 1
    assert isinstance(result.right, BinaryOpNode)
    assert result.right.op == TokenType.MULTIPLY


def test_parentheses_override_precedence():
    result = parse_or_error("(1+2)*3")
    _log("(1+2)*3", result)
    assert isinstance(result, BinaryOpNode)
    assert result.op == TokenType.MULTIPLY
    assert isinstance(result.left, GroupNode)
    assert isinstance(result.right, NumberNode) and result.right.value == 3


def test_power_right_associative():
    result = parse_or_error("2^3^4")
    _log("2^3^4", result)
    assert isinstance(result, BinaryOpNode)
    assert result.op == TokenType.POW
    assert isinstance(result.left, NumberNode) and result.left.value == 2
    assert isinstance(result.right, BinaryOpNode)
    assert result.right.op == TokenType.POW


@pytest.mark.parametrize(
    "source, op",
    [
        ("3-4", TokenType.MINUS),
        ("5*6", TokenType.MULTIPLY),
        ("7/2", TokenType.DIVIDE),
        ("2^3", TokenType.POW),
    ],
)
def test_binary_ops(source, op):
    result = parse_or_error(source)
    _log(source, result)
    assert isinstance(result, BinaryOpNode)
    assert result.op == op


# ============================================================
# 一元运算符
# ============================================================


def test_unary_minus():
    result = parse_or_error("-1")
    _log("-1", result)
    assert isinstance(result, UnaryOpNode)
    assert result.op == TokenType.MINUS
    assert isinstance(result.operand, NumberNode) and result.operand.value == 1


def test_unary_plus():
    result = parse_or_error("+2")
    _log("+2", result)
    assert isinstance(result, UnaryOpNode)
    assert result.op == TokenType.PLUS
    assert isinstance(result.operand, NumberNode) and result.operand.value == 2


def test_unary_in_expression():
    result = parse_or_error("-1+5")
    _log("-1+5", result)
    assert isinstance(result, BinaryOpNode)
    assert result.op == TokenType.PLUS
    assert isinstance(result.left, UnaryOpNode)
    assert isinstance(result.right, NumberNode) and result.right.value == 5


# ============================================================
# 骰子表达式
# ============================================================


def test_dice_basic():
    result = parse_or_error("1d6")
    _log("1d6", result)
    assert isinstance(result, DiceNode)
    assert isinstance(result.count, NumberNode) and result.count.value == 1
    assert isinstance(result.sides, NumberNode) and result.sides.value == 6
    assert result.selectors == []


def test_dice_in_expression():
    result = parse_or_error("2d6+3")
    _log("2d6+3", result)
    assert isinstance(result, BinaryOpNode)
    assert result.op == TokenType.PLUS
    assert isinstance(result.left, DiceNode)
    assert isinstance(result.right, NumberNode) and result.right.value == 3


# ============================================================
# 未实现功能
# ============================================================


@pytest.mark.parametrize(
    "source",
    [
        "x = 3d6",
    ],
)
def test_unimplemented_features(source):
    result = parse_or_error(source)
    _log(source, result)
    assert isinstance(result, ParserError)


# ============================================================
# Fuzzing 占位
# ============================================================


def test_fuzzing_parse():
    raise TodoError("test_fuzzing_parse")
