import pytest

from src.DiceLang.error import ParserError, TodoError
from src.DiceLang.lexer import Lexer
from src.DiceLang.parser import Parser
from src.DiceLang.astnode import (
    AstNode,
    BinaryOpNode,
    DiceNode,
    GroupNode,
    NumberNode,
    UnaryOpNode,
)
from src.DiceLang.tokens import TokenType


# --- 辅助函数 ---
def parse(source: str) -> AstNode:
    """把源字符串经 Lexer -> Parser 返回 AST。"""
    return Parser(Lexer(source).tokens).ast


# ============================================================
# 括号与分组 — 来自手动测试记录
# ============================================================

@pytest.mark.parametrize("source, expected_str", [
    ("(1)", "( 1 )"),
    ("((1))", "( ( 1 ) )"),
    ("((1)+(2))", "( (( 1 ) + ( 2 )) )"),
])
def test_group_happy(source, expected_str):
    assert str(parse(source)) == expected_str


@pytest.mark.parametrize("source", [
    "()",           # 空括号
    "((1)",         # 缺少右括号
    "(1))",         # 多余右括号
    "(1)+)",        # 右括号出现在中缀位置
    "(1)+(",        # 表达式不完整
    "(1)(2)",       # 括号间缺少运算符
    "((1)(2))",     # 嵌套括号间缺少运算符
    "(1()2)",       # 空括号出现在参数位置
    "(1+()2)",      # 空括号出现在运算中
    "((1)+2",       # 缺少闭合括号
    "1+(2))",       # 多余右括号
    "(1)+(2))",     # 多余右括号
    "(1+(2)3)",     # 数字出现在中缀位置
    "(1+2)3",       # 数字出现在中缀位置
    "(1+(2*3)",     # 缺少闭合括号
])
def test_group_error(source):
    with pytest.raises(ParserError):
        parse(source)


# ============================================================
# 基本算术
# ============================================================

@pytest.mark.parametrize("source, expected_str", [
    ("1+2", "(1 + 2)"),
    ("3-4", "(3 - 4)"),
    ("5*6", "(5 * 6)"),
    ("7/2", "(7 / 2)"),
    ("2^3", "(2 ^ 3)"),
    ("1+2*3", "(1 + (2 * 3))"),         # 乘法优先于加法
    ("(1+2)*3", "((( 1 ) + ( 2 )) * 3)"),  # 括号改变优先级
    ("2^3^4", "(2 ^ (3 ^ 4))"),          # 幂运算是右结合
])
def test_arithmetic_precedence(source, expected_str):
    assert str(parse(source)) == expected_str


# ============================================================
# 一元运算符
# ============================================================

@pytest.mark.parametrize("source, expected_str", [
    ("-1", "(-1)"),
    ("+2", "(+2)"),
    ("-1+5", "((-1) + 5)"),
    ("3+-2", "(3 + (-2))"),
])
def test_unary(source, expected_str):
    assert str(parse(source)) == expected_str


# ============================================================
# 骰子表达式
# ============================================================

@pytest.mark.parametrize("source, expected_str", [
    ("1d6", "(1 D 6)"),
    ("3d20", "(3 D 20)"),
    ("2d6+3", "((2 D 6) + 3)"),
])
def test_dice_basic(source, expected_str):
    assert str(parse(source)) == expected_str


# ============================================================
# 未实现功能 (应该抛 TodoError)
# ============================================================

@pytest.mark.parametrize("source", [
    "x = 3d6",       # 变量赋值
])
def test_unimplemented_features(source):
    with pytest.raises((TodoError, ParserError)):
        parse(source)


# ============================================================
# Fuzzing 占位
# ============================================================

def test_fuzzing_parse():
    """模糊测试：待实现。"""
    raise TodoError("test_fuzzing_parse")
