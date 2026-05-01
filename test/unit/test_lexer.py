import random
from typing import Any

import pytest

from DiceLang.astnode import AstNode
from DiceLang.error import DiceLangError, LexerError, TodoError
from DiceLang.lexer import Lexer
from DiceLang.tokens import (
    TokenType as tktype,
)

RNG = random.Random(42)  # 固定随机种子, 以便复现


# --- 辅助函数 ---
class _Color:
    RED = "\033[91m"
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    BOLD = "\033[1m"
    RESET = "\033[0m"


def lex_or_error(text: str) -> Lexer | DiceLangError:
    """词法分析并捕获错误，总是返回结果供测试打印。"""
    try:
        return Lexer(text)
    except DiceLangError as e:
        return e


def _log(source: str, result: Lexer | DiceLangError) -> None:
    is_err = isinstance(result, DiceLangError)
    tag = f"{_Color.RED}{_Color.BOLD}Error{_Color.RESET}" if is_err else f"{_Color.GREEN}OK{_Color.RESET}"
    raw = f"{_Color.YELLOW}{result}{_Color.RESET}" if is_err else str(result)
    indented = raw.replace("\n", "\n  ")
    print(f"\n  case={source!r}  [{tag}]\n  {indented}")


# ============================================================
# Fuzzing 占位
# ============================================================


@pytest.mark.xfail(reason="待实现", strict=True)
def test_fuzzing_lex():
    """模糊测试：随机生成合法的骰子表达式字符串，验证 Lexer 能正常解析。"""
    raise TodoError("test_fuzzing_lex")


# ============================================================
# 正常用例
# ============================================================


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
            [  # 连续减号: 词法阶段应输出两个 MINUS
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
    result = lex_or_error(text)
    _log(text, result)
    assert isinstance(result, Lexer), f"期望 Lexer，得到 {type(result).__name__}: {result}"
    tokens = result.tokens
    assert len(tokens) == len(expects) + 1  # expects少一个EOF
    for token, (type, value) in zip(tokens, expects, strict=False):
        assert token.type == type
        assert token.value == value
    assert tokens[-1].type == tktype.EOF


# ============================================================
# 错误样例
# ============================================================


@pytest.mark.parametrize(
    "bad_text",
    [
        "1@6**2",
    ],
)
def test_lex_invalid(bad_text):
    result = lex_or_error(bad_text)
    _log(bad_text, result)
    assert isinstance(result, LexerError), f"期望 LexerError，得到 {type(result).__name__}: {result}"
