import pytest

from dicelang.astnode import (
    AstNode,
    BinaryOpNode,
    ConditionMod,
    CountMod,
    DiceNode,
    GroupNode,
    HighestMod,
    KeepMod,
    LowestMod,
    MapMod,
    NumberNode,
    ThrowMod,
    UnaryOpNode,
)
from dicelang.error import DiceLangError, ParserError, TodoError
from dicelang.lexer import Lexer
from dicelang.parser import Parser
from dicelang.statement import ErrorStmt, ExprStmt, Statement, VarDefStmt
from dicelang.tokens import Token, TokenType


# --- 辅助函数 ---
class _Color:
    RED = "\033[91m"
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    BOLD = "\033[1m"
    RESET = "\033[0m"


def parse(source: str) -> AstNode:
    stmt = Parser(Lexer.tokenize(source)).parse()
    if isinstance(stmt, ErrorStmt):
        raise stmt.value  # 将 ErrorStmt 中的错误重新抛出，供 parse_or_error 捕获
    if isinstance(stmt, ExprStmt):
        return stmt.value
    raise TodoError("目前仅支持表达式语句的解析")


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
    assert result.selectors == ()


def test_dice_in_expression():
    result = parse_or_error("2d6+3")
    _log("2d6+3", result)
    assert isinstance(result, BinaryOpNode)
    assert result.op == TokenType.PLUS
    assert isinstance(result.left, DiceNode)
    assert isinstance(result.right, NumberNode) and result.right.value == 3


def test_dice_selectors_complex():
    """10d6 h4 l4 ifc >= 3 : (2d6) — ifc 展开为 if >= 3 c : (2d6)，CountMod 在 MapMod 之前"""
    result = parse_or_error("10d6 h4 l4 ifc >= 3 : (2d6)")
    _log("10d6 h4 l4 ifc >= 3 : (2d6)", result)
    assert isinstance(result, DiceNode)
    assert isinstance(result.selectors[0], HighestMod)
    assert result.selectors[0].count.value == 4
    assert isinstance(result.selectors[1], LowestMod)
    assert result.selectors[1].count.value == 4
    assert isinstance(result.selectors[2], ConditionMod)
    assert result.selectors[2].condition == TokenType.GTE
    assert result.selectors[2].threshold.value == 3
    assert isinstance(result.selectors[3], CountMod)  # c 紧跟 if
    assert isinstance(result.selectors[4], MapMod)     # : 在 c 之后（求值时会报错，count 先于 map）


def test_keyword_as_variable():
    """h = 5 → 关键字不能作为变量名"""
    result = parse_or_error("h = 5")
    _log("h = 5", result)
    assert isinstance(result, DiceLangError)


def test_keyword_in_macro():
    """&h = 5 → 关键字不能作为宏名"""
    result = parse_or_error("&h = 5")
    _log("&h = 5", result)
    assert isinstance(result, DiceLangError)


def test_selectors_in_arithmetic():
    """1 + h2 + l3 + :4 → 语法错误"""
    result = parse_or_error("1 + h2 + l3 + :4")
    _log("1 + h2 + l3 + :4", result)
    assert isinstance(result, DiceLangError)


# ============================================================
# 括号 + 选择器
# ============================================================


def test_paren_single_dice_with_selector():
    """(3d6)h2 → GroupNode 包裹 DiceNode，selectors 挂在 GroupNode"""
    result = parse_or_error("(3d6)h2")
    _log("(3d6)h2", result)
    assert isinstance(result, GroupNode)
    assert len(result.group) == 1
    assert isinstance(result.group[0], DiceNode)
    assert len(result.selectors) == 1
    assert isinstance(result.selectors[0], HighestMod)
    assert result.selectors[0].count.value == 2


def test_paren_single_dice_bare():
    """(2d8) → 纯括号包裹单骰，解析为 GroupNode（保留括号语义）"""
    result = parse_or_error("(2d8)")
    _log("(2d8)", result)
    assert isinstance(result, GroupNode)
    assert len(result.group) == 1
    assert isinstance(result.group[0], DiceNode)
    assert result.group[0].count.value == 2
    assert result.group[0].sides.value == 8
    assert result.selectors == ()


def test_paren_complex_with_selectors():
    """(2d8+1d6+2) h1 if >4 : 2 l1 t → 全部 5 个选择器链挂在 GroupNode"""
    result = parse_or_error("(2d8+1d6+2) h1 if >4 : 2 l1 t")
    _log("(2d8+1d6+2) h1 if >4 : 2 l1 t", result)
    assert isinstance(result, GroupNode)
    assert len(result.selectors) == 5
    assert isinstance(result.selectors[0], HighestMod)
    assert result.selectors[0].count.value == 1
    assert isinstance(result.selectors[1], ConditionMod)
    assert result.selectors[1].condition == TokenType.GT
    assert result.selectors[1].threshold.value == 4
    assert isinstance(result.selectors[2], MapMod)
    assert result.selectors[2].map_to.value == 2
    assert isinstance(result.selectors[3], LowestMod)
    assert result.selectors[3].count.value == 1
    assert isinstance(result.selectors[4], ThrowMod)


def test_paren_expr_with_selector():
    """(1d8+1d6)h1 → GroupNode 包裹 BinaryOpNode，selectors 挂在 GroupNode"""
    result = parse_or_error("(1d8+1d6)h1")
    _log("(1d8+1d6)h1", result)
    assert isinstance(result, GroupNode)
    assert len(result.group) == 1
    assert isinstance(result.group[0], BinaryOpNode)
    assert len(result.selectors) == 1
    assert isinstance(result.selectors[0], HighestMod)
    assert result.selectors[0].count.value == 1


def test_paren_expr_no_selector():
    """(1d8+1d6) → GroupNode 包裹 BinaryOpNode，无 selectors"""
    result = parse_or_error("(1d8+1d6)")
    _log("(1d8+1d6)", result)
    assert isinstance(result, GroupNode)
    assert len(result.group) == 1
    assert isinstance(result.group[0], BinaryOpNode)
    assert result.selectors == ()


# ============================================================
# 未实现功能
# ============================================================



# ============================================================
# VarDef 解析
# ============================================================


def parse_stmt(source: str) -> Statement:
    return Parser(Lexer.tokenize(source)).parse()


def parse_stmt_or_error(source: str) -> Statement | DiceLangError:
    try:
        return parse_stmt(source)
    except DiceLangError as e:
        return e


@pytest.mark.parametrize(
    ("source", "names", "expected"),
    [
        # 合法 VarDef
        ("x = 5", ("x",), "vardef"),
        ("foo, bar, baz = 3d6", ("foo", "bar", "baz"), "vardef"),
        ("x = 2 + 3 * 4", ("x",), "vardef"),
        ("x, y, = 5", ("x", "y"), "vardef"),  # 尾随逗号 OK
        # 复合赋值
        ("x += 5", ("x",), "vardef"),
        ("x -= 3", ("x",), "vardef"),
        ("x *= 2", ("x",), "vardef"),
        ("x /= 2", ("x",), "vardef"),
        ("x %= 3", ("x",), "vardef"),
        ("x ^= 2", ("x",), "vardef"),
        # 表达式（非 VarDef）
        ("x + y + z", (), "expr"),
        ("x", (), "expr"),
        # 错误：无变量名
        ("= 5", (), "error"),
        # 错误：表达式当名字
        ("x, y+1 = 5", (), "error"),
        # 错误：链式赋值
        ("x = y + 1 = z", (), "error"),
    ],
)
def test_vardef_parsing(source, names, expected):
    if expected == "error":
        result = parse_stmt_or_error(source)
    else:
        result = parse_stmt(source)
    _log(source, result)
    if expected == "vardef":
        assert isinstance(result, VarDefStmt)
        assert result.names == names
    elif expected == "expr":
        assert not isinstance(result, (VarDefStmt, ErrorStmt))
    else:
        assert isinstance(result, (ErrorStmt, DiceLangError))


# ============================================================
# Fuzzing 占位
# ============================================================


def test_fuzzing_parse():
    """随机表达式解析不崩溃，总是返回 Statement。"""
    import random as _random
    from dicelang.error import DiceLangError
    from dicelang.lexer import Lexer
    from dicelang.parser import Parser

    def _expr(rng, d=0):
        if d > 6:
            return str(rng.randint(1, 100))
        kinds = [
            lambda: str(rng.randint(1, 100)),
            lambda: f"{rng.randint(1, 6)}d{rng.randint(2, 12)}",
            lambda: f"({_expr(rng, d + 1)})",
        ]
        if d > 0:
            kinds.extend([
                lambda: f"{_expr(rng, d + 1)} + {_expr(rng, d + 1)}",
                lambda: f"{_expr(rng, d + 1)} * {_expr(rng, d + 1)}",
            ])
        return rng.choice(kinds)()

    rng = _random.Random(42)
    ok = 0
    for _ in range(50):
        expr = _expr(rng)
        try:
            tokens = Lexer.tokenize(expr)
            stmt = Parser(tokens).parse()
            assert stmt is not None
            ok += 1
        except DiceLangError:
            ok += 1
        except Exception as e:
            pytest.fail(f"未预期的异常 [{expr}]: {type(e).__name__}: {e}")
    assert ok == 50


# ============================================================
# 故意失败
# ============================================================
@pytest.mark.xfail(reason="故意失败, 用于测试框架", strict=True)
@pytest.mark.parametrize("source", ["max(1, 2)"])
def test_intentional_failure(source):
    result = parse_or_error(source)
    _log(source, result)
    assert isinstance(result, ParserError)


# ============================================================
# 对刻意构造的Token失败
# ============================================================


@pytest.mark.xfail(reason="故意失败, 用于测试框架", strict=True)
@pytest.mark.parametrize("source", [[Token(TokenType.PLUS, "+", "+", 0), Token(TokenType.NUMBER, "1", "1", 1)]])
def test_intentional_bad_tokens_failure(source):
    """测试框架的故意失败情况"""

    def parse_or_error_without_lexer(s):
        try:
            return Parser(s).parse_expr()
        except DiceLangError as e:
            return e

    result = parse_or_error_without_lexer(source)
    _log(str(source), result)
    assert not isinstance(result, (ParserError, TodoError))
