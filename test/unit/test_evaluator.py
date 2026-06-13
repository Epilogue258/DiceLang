import random

import pytest

from DiceLang.astnode import AstNode, BinaryOpNode, NumberNode, UnaryOpNode, VarNode
from DiceLang.error import DiceLangError, TodoError
from DiceLang.evaluator import Evaluator
from DiceLang.result import ErrorRes, ExprRes, VarDefRes, VarInfo
from DiceLang.tokens import TokenType as tktype
from DiceLang.statement import ExprStmt, VarDefStmt

RNG = random.Random(42)  # 固定随机种子, 以便复现
_P = 0  # 测试用占位 pos/length


# --- 辅助函数 ---
class _Color:
    RED = "\033[91m"
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    BOLD = "\033[1m"
    RESET = "\033[0m"


def eval_final(node: AstNode) -> int | DiceLangError:
    """求值并返回最终整数结果，捕获错误。"""
    try:
        result = Evaluator(rng=RNG).eval(ExprStmt(value=node))
        if isinstance(result, ErrorRes):
            return result.value
        assert isinstance(result, ExprRes)
        return result.value
    except DiceLangError as e:
        return e


def _log(desc: str, result) -> None:
    is_err = isinstance(result, (DiceLangError, ErrorRes))
    tag = f"{_Color.RED}{_Color.BOLD}Error{_Color.RESET}" if is_err else f"{_Color.GREEN}OK{_Color.RESET}"
    raw = f"{_Color.YELLOW}{result.value}{_Color.RESET}" if isinstance(result, ErrorRes) else (
        f"{_Color.YELLOW}{result}{_Color.RESET}" if is_err else str(result)
    )
    indented = raw.replace("\n", "\n  ")
    print(f"\n  case={desc!r}  [{tag}]\n  {indented}")


# ============================================================
# 算术表达式
# ============================================================


def test_arithmetic_complex():
    """测试算术表达式 (1+1+1)*(1+1)+(1+1) = 8"""
    num1 = NumberNode(value=1, pos=_P, length=_P)
    plus1_1 = BinaryOpNode(op=tktype.PLUS, left=num1, right=num1, pos=_P, length=_P)
    plus1_1_1 = BinaryOpNode(op=tktype.PLUS, left=plus1_1, right=num1, pos=_P, length=_P)
    mult = BinaryOpNode(op=tktype.MULTIPLY, left=plus1_1_1, right=plus1_1, pos=_P, length=_P)
    expr = BinaryOpNode(op=tktype.PLUS, left=mult, right=plus1_1, pos=_P, length=_P)

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
    from DiceLang.lexer import Lexer
    from DiceLang.parser import Parser

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
    inner = BinaryOpNode(op=tktype.POW, left=NumberNode(value=3, pos=_P, length=_P), right=NumberNode(value=2, pos=_P, length=_P))
    expr = BinaryOpNode(op=tktype.POW, left=NumberNode(value=2, pos=_P, length=_P), right=inner, pos=_P, length=_P)

    result = eval_final(expr)
    _log("2^3^2", result)
    assert not isinstance(result, DiceLangError)
    assert result == 512


# ============================================================
# 一元运算符
# ============================================================


def test_unary_minus_number():
    node = UnaryOpNode(op=tktype.MINUS, operand=NumberNode(value=42, pos=_P, length=_P), pos=_P, length=_P)
    result = eval_final(node)
    _log("-42", result)
    assert not isinstance(result, DiceLangError)
    assert result == -42


def test_unary_plus_number():
    node = UnaryOpNode(op=tktype.PLUS, operand=NumberNode(value=7, pos=_P, length=_P), pos=_P, length=_P)
    result = eval_final(node)
    _log("+7", result)
    assert not isinstance(result, DiceLangError)
    assert result == 7


# ============================================================
# Fuzzing 占位
# ============================================================


@pytest.mark.xfail(reason="待实现", strict=True, raises=TodoError)
def test_fuzzing_eval():
    raise TodoError("test_fuzzing_eval")


# ============================================================
# VarDef（手工构造 Statement，测试 Evaluator 层的变量赋值语义）
# ============================================================


def test_vardef_simple():
    """x = 5"""
    stmt = VarDefStmt(names=("x",), expr=NumberNode(value=5, pos=_P, length=_P))
    result = Evaluator().eval(stmt)
    _log("x = 5", result)
    assert isinstance(result, VarDefRes)
    assert result.vars == (VarInfo(name="x", old=None, value=5),)


def test_vardef_expression():
    """x = 2 + 3"""
    expr = BinaryOpNode(op=tktype.PLUS, left=NumberNode(value=2, pos=_P, length=_P), right=NumberNode(value=3, pos=_P, length=_P))
    stmt = VarDefStmt(names=("x",), expr=expr)
    result = Evaluator().eval(stmt)
    _log("x = 2 + 3", result)
    assert isinstance(result, VarDefRes)
    assert result.vars[0].value == 5


def test_vardef_reassign():
    """x = 5; x = x + 3"""
    evaluator = Evaluator()
    r1 = evaluator.eval(VarDefStmt(names=("x",), expr=NumberNode(value=5, pos=_P, length=_P)))
    _log("x = 5", r1)
    assert isinstance(r1, VarDefRes)
    assert r1.vars == (VarInfo(name="x", old=None, value=5),)

    expr = BinaryOpNode(op=tktype.PLUS, left=VarNode(name="x", pos=_P, length=_P), right=NumberNode(value=3, pos=_P, length=_P))
    r2 = evaluator.eval(VarDefStmt(names=("x",), expr=expr))
    _log("x = x + 3", r2)
    assert isinstance(r2, VarDefRes)
    assert r2.vars == (VarInfo(name="x", old=5, value=8),)


def test_vardef_use_var_in_expr():
    """x = 5; x + 3"""
    evaluator = Evaluator()
    evaluator.eval(VarDefStmt(names=("x",), expr=NumberNode(value=5, pos=_P, length=_P)))
    stmt = ExprStmt(value=BinaryOpNode(op=tktype.PLUS, left=VarNode(name="x", pos=_P, length=_P), right=NumberNode(value=3, pos=_P, length=_P)))
    result = evaluator.eval(stmt)
    _log("x = 5; x + 3", result)
    assert isinstance(result, ExprRes)
    assert result.value == 8


def test_vardef_multi_names():
    """a, b = 10"""
    stmt = VarDefStmt(names=("a", "b"), expr=NumberNode(value=10, pos=_P, length=_P))
    result = Evaluator().eval(stmt)
    _log("a, b = 10", result)
    assert isinstance(result, VarDefRes)
    assert result.vars == (
        VarInfo(name="a", old=None, value=10),
        VarInfo(name="b", old=None, value=10),
    )


def test_vardef_undefined_variable():
    """y = z + 1（z 未定义）"""
    expr = BinaryOpNode(op=tktype.PLUS, left=VarNode(name="z", pos=_P, length=_P), right=NumberNode(value=1, pos=_P, length=_P))
    stmt = VarDefStmt(names=("y",), expr=expr)
    result = Evaluator().eval(stmt)
    _log("y = z + 1 (z 未定义)", result)
    assert isinstance(result, ErrorRes)


def test_compound_assign():
    """x = 5; x += 3 → old=5, value=8"""
    evaluator = Evaluator()
    evaluator.eval(VarDefStmt(names=("x",), expr=NumberNode(value=5, pos=_P, length=_P)))
    stmt = VarDefStmt(names=("x",), expr=NumberNode(value=3, pos=_P, length=_P), op=tktype.PLUS_ASSIGN)
    result = evaluator.eval(stmt)
    _log("x += 3", result)
    assert isinstance(result, VarDefRes)
    assert result.vars[0].old == 5
    assert result.vars[0].value == 8


def test_compound_divide_by_zero():
    """x = 5; x /= 0 → ErrorRes"""
    evaluator = Evaluator()
    evaluator.eval(VarDefStmt(names=("x",), expr=NumberNode(value=5, pos=_P, length=_P)))
    stmt = VarDefStmt(names=("x",), expr=NumberNode(value=0, pos=_P, length=_P), op=tktype.DIVIDE_ASSIGN)
    result = evaluator.eval(stmt)
    _log("x /= 0", result)
    assert isinstance(result, ErrorRes)


def test_compound_undefined():
    """x += 5（x 未定义）→ ErrorRes"""
    stmt = VarDefStmt(names=("x",), expr=NumberNode(value=5, pos=_P, length=_P), op=tktype.PLUS_ASSIGN)
    result = Evaluator().eval(stmt)
    _log("x += 5 (x 未定义)", result)
    assert isinstance(result, ErrorRes)
