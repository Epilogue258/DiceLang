import random

import pytest

from dicelang.astnode import AstNode, BinaryOpNode, FuncCallNode, GroupNode, NumberNode, UnaryOpNode, VarNode
from dicelang.error import DiceLangError, TodoError
from dicelang.evaluator import Evaluator
from dicelang.result import ErrorRes, ExprRes, VarDefRes, VarInfo
from dicelang.statement import ExprStmt, VarDefStmt
from dicelang.tokens import TokenType as tktype

RNG = random.Random(42)  # 固定随机种子, 以便复现


def N(cls, **kwargs):
    """构造 AST 节点，自动填充 pos=0, length=0。"""
    kwargs.setdefault("pos", 0)
    kwargs.setdefault("length", 0)
    return cls(**kwargs)


# --- 辅助函数 ---
class _Color:
    RED = "\033[91m"
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    BOLD = "\033[1m"
    RESET = "\033[0m"


def eval_final(node: AstNode) -> int | DiceLangError:
    """求值并返回最终整数结果，捕获错误。每次使用独立 RNG。"""
    try:
        result = Evaluator(rng=random.Random(42)).eval(ExprStmt(value=node))
        if isinstance(result, ErrorRes):
            return result.value
        assert isinstance(result, ExprRes)
        return result.value
    except DiceLangError as e:
        return e


def _log(desc: str, result) -> None:
    is_err = isinstance(result, (DiceLangError, ErrorRes))
    tag = f"{_Color.RED}{_Color.BOLD}Error{_Color.RESET}" if is_err else f"{_Color.GREEN}OK{_Color.RESET}"
    raw = (
        f"{_Color.YELLOW}{result.value}{_Color.RESET}"
        if isinstance(result, ErrorRes)
        else (f"{_Color.YELLOW}{result}{_Color.RESET}" if is_err else str(result))
    )
    indented = raw.replace("\n", "\n  ")
    print(f"\n  case={desc!r}  [{tag}]\n  {indented}")


# ============================================================
# 算术表达式
# ============================================================


def test_arithmetic_complex():
    """测试算术表达式 (1+1+1)*(1+1)+(1+1) = 8"""
    num1 = N(NumberNode, value=1)
    plus1_1 = N(BinaryOpNode, op=tktype.PLUS, left=num1, right=num1)
    plus1_1_1 = N(BinaryOpNode, op=tktype.PLUS, left=plus1_1, right=num1)
    mult = N(BinaryOpNode, op=tktype.MULTIPLY, left=plus1_1_1, right=plus1_1)
    expr = N(BinaryOpNode, op=tktype.PLUS, left=mult, right=plus1_1)

    result = eval_final(expr)
    _log("(1+1+1)*(1+1)+(1+1)", result)
    assert not isinstance(result, DiceLangError)
    assert result == 8


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
    from dicelang.lexer import Lexer
    from dicelang.parser import Parser

    stmt = Parser(Lexer.tokenize(expr)).parse()
    if isinstance(stmt, ExprStmt):
        ast = stmt.value
    else:
        raise TodoError("目前仅支持表达式语句的求值")

    result = eval_final(ast)
    _log(expr, result)
    assert not isinstance(result, DiceLangError)
    assert result == expected


# ============================================================
# 幂运算右结合
# ============================================================


def test_power_right_associative():
    """2^3^2 = 2^(3^2) = 2^9 = 512"""
    # 手写: 2^(3^2)
    inner = N(BinaryOpNode, op=tktype.POW, left=N(NumberNode, value=3), right=N(NumberNode, value=2))
    expr = N(BinaryOpNode, op=tktype.POW, left=N(NumberNode, value=2), right=inner)

    result = eval_final(expr)
    _log("2^3^2", result)
    assert not isinstance(result, DiceLangError)
    assert result == 512


# ============================================================
# 一元运算符
# ============================================================


def test_unary_minus_number():
    node = N(UnaryOpNode, op=tktype.MINUS, operand=N(NumberNode, value=42))
    result = eval_final(node)
    _log("-42", result)
    assert not isinstance(result, DiceLangError)
    assert result == -42


def test_unary_plus_number():
    node = N(UnaryOpNode, op=tktype.PLUS, operand=N(NumberNode, value=7))
    result = eval_final(node)
    _log("+7", result)
    assert not isinstance(result, DiceLangError)
    assert result == 7


# ============================================================
# Fuzzing 占位
# ============================================================


def test_fuzzing_eval():
    """随机表达式求值不崩溃，结果可迭代。"""
    import random as _random

    from dicelang.error import DiceLangError
    from dicelang.evaluator import Evaluator
    from dicelang.lexer import Lexer
    from dicelang.parser import Parser

    def _expr(rng, d=0):
        if d > 6:
            return str(rng.randint(1, 20))
        kinds = [
            lambda: str(rng.randint(1, 20)),
            lambda: f"{rng.randint(1, 4)}d{rng.randint(2, 10)}",
            lambda: f"({_expr(rng, d + 1)})",
        ]
        if d > 0:
            kinds.extend([
                lambda: f"{_expr(rng, d + 1)} + {_expr(rng, d + 1)}",
                lambda: f"{_expr(rng, d + 1)} - {_expr(rng, d + 1)}",
            ])
        sel = ["h1", "l1", "k", "t", "if>2", "if<6", "count", "!", "e", "re"]
        e = rng.choice(kinds)()
        if rng.random() < 0.2:
            e += rng.choice(sel)
        return e

    rng = _random.Random(42)
    ok = 0
    for _ in range(50):
        expr = _expr(rng)
        try:
            tokens = Lexer.tokenize(expr)
            stmt = Parser(tokens).parse()
            res = Evaluator(rng=_random.Random(rng.randint(0, 2**31 - 1))).eval(stmt)
            if hasattr(res, "__iter__"):
                list(res)
            ok += 1
        except DiceLangError:
            ok += 1
        except Exception as e:
            pytest.fail(f"未预期的异常 [{expr}]: {type(e).__name__}: {e}")
    assert ok == 50


# ============================================================
# VarDef（手工构造 Statement，测试 Evaluator 层的变量赋值语义）
# ============================================================


def test_vardef_simple():
    """x = 5"""
    stmt = VarDefStmt(names=("x",), expr=N(NumberNode, value=5))
    result = Evaluator().eval(stmt)
    _log("x = 5", result)
    assert isinstance(result, VarDefRes)
    assert result.vars == (VarInfo(name="x", old=None, value=5),)


def test_vardef_expression():
    """x = 2 + 3"""
    expr = BinaryOpNode(op=tktype.PLUS, left=N(NumberNode, value=2), right=N(NumberNode, value=3))
    stmt = VarDefStmt(names=("x",), expr=expr)
    result = Evaluator().eval(stmt)
    _log("x = 2 + 3", result)
    assert isinstance(result, VarDefRes)
    assert result.vars[0].value == 5


def test_vardef_reassign():
    """x = 5; x = x + 3"""
    evaluator = Evaluator()
    r1 = evaluator.eval(VarDefStmt(names=("x",), expr=N(NumberNode, value=5)))
    _log("x = 5", r1)
    assert isinstance(r1, VarDefRes)
    assert r1.vars == (VarInfo(name="x", old=None, value=5),)

    expr = N(BinaryOpNode, op=tktype.PLUS, left=N(VarNode, name="x"), right=N(NumberNode, value=3))
    r2 = evaluator.eval(VarDefStmt(names=("x",), expr=expr))
    _log("x = x + 3", r2)
    assert isinstance(r2, VarDefRes)
    assert r2.vars == (VarInfo(name="x", old=5, value=8),)


def test_vardef_use_var_in_expr():
    """x = 5; x + 3"""
    evaluator = Evaluator()
    evaluator.eval(VarDefStmt(names=("x",), expr=N(NumberNode, value=5)))
    stmt = ExprStmt(value=N(BinaryOpNode, op=tktype.PLUS, left=N(VarNode, name="x"), right=N(NumberNode, value=3)))
    result = evaluator.eval(stmt)
    _log("x = 5; x + 3", result)
    assert isinstance(result, ExprRes)
    assert result.value == 8


def test_vardef_multi_names():
    """a, b = 10"""
    stmt = VarDefStmt(names=("a", "b"), expr=N(NumberNode, value=10))
    result = Evaluator().eval(stmt)
    _log("a, b = 10", result)
    assert isinstance(result, VarDefRes)
    assert result.vars == (
        VarInfo(name="a", old=None, value=10),
        VarInfo(name="b", old=None, value=10),
    )


def test_vardef_undefined_variable():
    """y = z + 1（z 未定义）"""
    expr = N(BinaryOpNode, op=tktype.PLUS, left=N(VarNode, name="z"), right=N(NumberNode, value=1))
    stmt = VarDefStmt(names=("y",), expr=expr)
    result = Evaluator().eval(stmt)
    _log("y = z + 1 (z 未定义)", result)
    assert isinstance(result, ErrorRes)


def test_compound_assign():
    """x = 5; x += 3 → old=5, value=8"""
    evaluator = Evaluator()
    evaluator.eval(VarDefStmt(names=("x",), expr=N(NumberNode, value=5)))
    stmt = VarDefStmt(names=("x",), expr=N(NumberNode, value=3), op=tktype.PLUS_ASSIGN)
    result = evaluator.eval(stmt)
    _log("x += 3", result)
    assert isinstance(result, VarDefRes)
    assert result.vars[0].old == 5
    assert result.vars[0].value == 8


def test_compound_divide_by_zero():
    """x = 5; x /= 0 → ErrorRes"""
    evaluator = Evaluator()
    evaluator.eval(VarDefStmt(names=("x",), expr=N(NumberNode, value=5)))
    stmt = VarDefStmt(names=("x",), expr=N(NumberNode, value=0), op=tktype.DIVIDE_ASSIGN)
    result = evaluator.eval(stmt)
    _log("x /= 0", result)
    assert isinstance(result, ErrorRes)


def test_compound_undefined():
    """x += 5（x 未定义）→ ErrorRes"""
    stmt = VarDefStmt(names=("x",), expr=N(NumberNode, value=5), op=tktype.PLUS_ASSIGN)
    result = Evaluator().eval(stmt)
    _log("x += 5 (x 未定义)", result)
    assert isinstance(result, ErrorRes)


# ============================================================
# FuncCall（max / min）
# ============================================================


def test_func_max_basic():
    """max(1, 2, 3) → 3"""
    result = eval_final(N(FuncCallNode, func="max", args=GroupNode(group=[
        N(NumberNode, value=1), N(NumberNode, value=2), N(NumberNode, value=3),
    ])))
    _log("max(1,2,3)", result)
    assert not isinstance(result, DiceLangError)
    assert result == 3


def test_func_min_basic():
    """min(5, 2, 8) → 2"""
    result = eval_final(N(FuncCallNode, func="min", args=GroupNode(group=[
        N(NumberNode, value=5), N(NumberNode, value=2), N(NumberNode, value=8),
    ])))
    _log("min(5,2,8)", result)
    assert not isinstance(result, DiceLangError)
    assert result == 2


def test_func_max_with_arithmetic():
    """max(2+3, 3*4) → max(5, 12) → 12"""
    from dicelang.lexer import Lexer
    from dicelang.parser import Parser

    stmt = Parser(Lexer.tokenize("max(2+3, 3*4)")).parse()
    result = eval_final(stmt.value)
    _log("max(2+3, 3*4)", result)
    assert not isinstance(result, DiceLangError)
    assert result == 12


def test_func_nested():
    """max(max(1,2), min(5,3)) → max(2, 3) → 3"""
    from dicelang.lexer import Lexer
    from dicelang.parser import Parser

    stmt = Parser(Lexer.tokenize("max(max(1,2), min(5,3))")).parse()
    result = eval_final(stmt.value)
    _log("max(max(1,2), min(5,3))", result)
    assert not isinstance(result, DiceLangError)
    assert result == 3


def test_func_max_with_dice():
    """max(2d6, 3d6) → max([6,1], [6,3,1]) → max(7, 10) → 10"""
    from dicelang.lexer import Lexer
    from dicelang.parser import Parser

    stmt = Parser(Lexer.tokenize("max(2d6, 3d6)")).parse()
    result = eval_final(stmt.value)
    _log("max(2d6, 3d6)", result)
    assert not isinstance(result, DiceLangError)
    assert result == 10


@pytest.mark.xfail(reason="lexer 将 dmax 视为单 token，未拆分为 DICE + IDENTIFIER", strict=True)
def test_func_dice_with_func_sides():
    """1dmax(4,6) → 词法粘连，xfail"""
    from dicelang.lexer import Lexer
    from dicelang.parser import Parser
    from dicelang.statement import ErrorStmt

    stmt = Parser(Lexer.tokenize("1dmax(4,6)")).parse()
    if isinstance(stmt, ErrorStmt):
        raise stmt.value  # strict xfail 要求抛异常


@pytest.mark.xfail(reason="lexer 将 dmin 视为单 token，未拆分为 DICE + IDENTIFIER", strict=True)
def test_func_dice_with_func_count_and_sides_nospace():
    """max(2,3)dmin(4,6) → 词法粘连，xfail"""
    from dicelang.lexer import Lexer
    from dicelang.parser import Parser
    from dicelang.statement import ErrorStmt

    stmt = Parser(Lexer.tokenize("max(2,3)dmin(4,6)")).parse()
    if isinstance(stmt, ErrorStmt):
        raise stmt.value


# ============================================================
# FuncCall + Dice（空格/括号断开粘连的版本）
# ============================================================


def test_func_dice_with_func_sides_spaced():
    """1 d max(4,6) → 1d6 → 6"""
    from dicelang.lexer import Lexer
    from dicelang.parser import Parser

    stmt = Parser(Lexer.tokenize("1 d max(4,6)")).parse()
    result = eval_final(stmt.value)
    _log("1 d max(4,6)", result)
    assert not isinstance(result, DiceLangError)
    assert result == 6


def test_func_dice_with_func_count_and_sides_spaced():
    """max(2,3) d min(4,6) → 3d4 → 5"""
    from dicelang.lexer import Lexer
    from dicelang.parser import Parser

    stmt = Parser(Lexer.tokenize("max(2,3) d min(4,6)")).parse()
    result = eval_final(stmt.value)
    _log("max(2,3) d min(4,6)", result)
    assert not isinstance(result, DiceLangError)
    assert result == 5


def test_func_dice_with_func_parens():
    """(max(4,6))d(min(2,3)) → 6d3 → 7（)d( 自然断开粘连）"""
    from dicelang.lexer import Lexer
    from dicelang.parser import Parser

    stmt = Parser(Lexer.tokenize("(max(4,6))d(min(2,3))")).parse()
    result = eval_final(stmt.value)
    _log("(max(4,6))d(min(2,3))", result)
    assert not isinstance(result, DiceLangError)
    assert result == 7


def test_func_dice_with_func_parens_spaced():
    """(max(4,6)) d (min(2,3)) → 6d3 → 7"""
    from dicelang.lexer import Lexer
    from dicelang.parser import Parser

    stmt = Parser(Lexer.tokenize("(max(4,6)) d (min(2,3))")).parse()
    result = eval_final(stmt.value)
    _log("(max(4,6)) d (min(2,3))", result)
    assert not isinstance(result, DiceLangError)
    assert result == 7


def test_func_dice_with_func_swapped_spaced():
    """max(4,6) d min(2,3) → 6d3 → 7"""
    from dicelang.lexer import Lexer
    from dicelang.parser import Parser

    stmt = Parser(Lexer.tokenize("max(4,6) d min(2,3)")).parse()
    result = eval_final(stmt.value)
    _log("max(4,6) d min(2,3)", result)
    assert not isinstance(result, DiceLangError)
    assert result == 7
