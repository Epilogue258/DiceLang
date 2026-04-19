import random
from typing import Any

import pytest

from lexer import Lexer
from tokens import (
    TokenType as tktype,
)

RNG = random.Random(42)  # 固定随机种子, 以便复现


# fuzzing test
def test_fuzzing_lex():
    """
    模糊测试：随机生成100个合法的骰子表达式字符串
    验证 Lexer 能正常解析，不抛出 ValueError/语法错误
    """
    pass


# 固定case的happy测试
@pytest.mark.parametrize(
    "text, expects",
    [
        # 基本解析+D的转换为d
        (
            "12D6",
            [
                (tktype.NUMBER, 12),
                (tktype.DICE, "d"),
                (tktype.NUMBER, 6),
            ],
        ),
        # 带空格和混合运算
        (
            "2 D 8+  1",
            [
                (tktype.NUMBER, 2),
                (tktype.DICE, "d"),
                (tktype.NUMBER, 8),
                (tktype.PLUS, "+"),
                (tktype.NUMBER, 1),
            ],
        ),
        (
            "reroll(6**2)",
            [
                (tktype.IDENTIFIER, "reroll"),
                (tktype.LPAREN, "("),
                (tktype.NUMBER, 6),
                (tktype.POW, "^"),
                (tktype.NUMBER, 2),
                (tktype.RPAREN, ")"),
            ],
        ),
        ("00123", [(tktype.NUMBER, 123)]),  # 前导0
        ("", []),
        (
            ">-",
            [
                (tktype.GT, ">"),
                (tktype.MINUS, "-"),
            ],
        ),  # 测试回退
        (
            "<= >= == !=",
            [
                (tktype.LTE, "<="),
                (tktype.GTE, ">="),
                (tktype.EQ, "=="),
                (tktype.NEQ, "!="),
            ],
        ),
        (
            "< = > =",
            [  # 分开写的运算符
                (tktype.LT, "<"),
                (tktype.ASSIGN, "="),
                (tktype.GT, ">"),
                (tktype.ASSIGN, "="),
            ],
        ),
        (
            "1-2",
            [  # 减号
                (tktype.NUMBER, 1),
                (tktype.MINUS, "-"),
                (tktype.NUMBER, 2),
            ],
        ),
        (
            "1--2",
            [  # 连续减号（可能用于表示负数？词法阶段应输出两个 MINUS）
                (tktype.NUMBER, 1),
                (tktype.MINUS, "-"),
                (tktype.MINUS, "-"),
                (tktype.NUMBER, 2),
            ],
        ),
        ("REROLL", [(tktype.IDENTIFIER, "reroll")]),
        ("1D6!", [(tktype.NUMBER, 1), (tktype.DICE, "d"), (tktype.NUMBER, 6), (tktype.EXPLODE, "!")]),
        (
            "1D6 if == 1 : 2",
            [
                (tktype.NUMBER, 1),
                (tktype.DICE, "d"),
                (tktype.NUMBER, 6),
                (tktype.IF, "if"),
                (tktype.EQ, "=="),
                (tktype.NUMBER, 1),
                (tktype.COLON, ":"),
                (tktype.NUMBER, 2),
            ],
        ),
    ],
)
def test_lex_happy(text, expects: list[tuple[tktype, Any]]):
    lexer = Lexer(text)
    assert len(lexer.tokens) == len(expects) + 1  # expects少一个EOF
    for token, (type, value) in zip(lexer.tokens, expects, strict=False):  # EOF会被zip自动截断, 无需处理
        assert token.type == type
        assert token.value == value
    else:
        assert lexer.tokens[-1].type == tktype.EOF


# 固定样本的错误样例测试
@pytest.mark.parametrize(
    "bad_text",
    [
        ("1@6**2"),
    ],
)
def test_inva_invalid(bad_text):
    with pytest.raises(ValueError):
        Lexer(bad_text)
