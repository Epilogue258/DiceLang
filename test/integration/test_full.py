"""
集成测试：Lexer → Parser → Evaluator 全链路
输入字符串，验证最终求值结果。
"""

import random

import pytest

from DiceLang.error import DiceLangError, TodoError
from DiceLang.evaluator import Evaluator
from DiceLang.lexer import Lexer
from DiceLang.parser import Parser
from DiceLang.result import ErrorRes, ExprRes

RNG = random.Random(42)  # 固定随机种子, 以便复现


# --- 辅助函数 ---
class _Color:
    RED = "\033[91m"
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    BOLD = "\033[1m"
    RESET = "\033[0m"


def eval_str(source: str, rng: random.Random = RNG) -> ExprRes | DiceLangError:
    """从字符串走完整链路求值，返回 ExprRes 或错误。"""
    try:
        tokens = Lexer.tokenize(source)
        stmt = Parser(tokens).parse()
        result = Evaluator(rng=rng).eval(stmt)
        if isinstance(result, ErrorRes):
            return result.value
        assert isinstance(result, ExprRes), f"期望 ExprRes, 得到 {type(result).__name__}: {result}"
        return result
    except DiceLangError as e:
        return e


def eval_steps(source: str, rng: random.Random = RNG) -> list[str] | DiceLangError:
    """从字符串走完整链路，返回每一步化简的字符串表示。"""
    try:
        tokens = Lexer.tokenize(source)
        stmt = Parser(tokens).parse()
        result = Evaluator(rng=rng).eval(stmt)
        if isinstance(result, ErrorRes):
            return result.value
        assert isinstance(result, ExprRes), f"期望 ExprRes, 得到 {type(result).__name__}"
        return list(result.steps)
    except DiceLangError as e:
        return e


def _log(source: str, result) -> None:
    is_err = isinstance(result, DiceLangError)
    tag = f"{_Color.RED}{_Color.BOLD}Error{_Color.RESET}" if is_err else f"{_Color.GREEN}OK{_Color.RESET}"
    raw = f"{_Color.YELLOW}{result}{_Color.RESET}" if is_err else str(result)
    indented = raw.replace("\n", "\n  ")
    print(f"\n  case={source!r}  [{tag}]\n  {indented}")


# ============================================================
# 基本算术
# ============================================================


@pytest.mark.parametrize(
    "source, expected",
    [
        ("1 + 2", 3),
        ("10 - 3", 7),
        ("4 * 5", 20),
        ("7 / 2", 3),  # 地板除
        ("7 % 3", 1),
        ("2 ^ 10", 1024),
        ("0 + 0", 0),
        ("1 - 1", 0),
        ("0 * 999", 0),
    ],
)
def test_arithmetic_basic(source, expected: int):
    result = eval_str(source)
    _log(source, result)
    assert isinstance(result, ExprRes), f"期望 ExprRes, 得到 {type(result).__name__}: {result}"
    assert result.value == expected


# ============================================================
# 运算符优先级
# ============================================================


@pytest.mark.parametrize(
    "source, expected",
    [
        ("1 + 2 * 3", 7),  # 1+(2*3)
        ("2 * 3 + 1", 7),  # (2*3)+1
        ("2 + 3 ^ 2", 11),  # 2+(3^2)
        ("2 ^ 3 * 4", 32),  # (2^3)*4
        ("(1 + 2) * 3", 9),  # 括号覆盖优先级
        ("(2 + 3) ^ 2", 25),
        ("2 * (3 + 4)", 14),
    ],
)
def test_precedence(source, expected: int):
    result = eval_str(source)
    _log(source, result)
    assert isinstance(result, ExprRes)
    assert result.value == expected


# ============================================================
# 幂运算右结合
# ============================================================


@pytest.mark.parametrize(
    "source, expected",
    [
        ("2 ^ 3 ^ 2", 512),  # 2^(3^2) = 2^9 = 512
        ("3 ^ 1 ^ 5", 3),  # 3^(1^5) = 3^1 = 3
    ],
)
def test_power_right_associative(source, expected: int):
    result = eval_str(source)
    _log(source, result)
    assert isinstance(result, ExprRes)
    assert result.value == expected


# ============================================================
# 一元运算符
# ============================================================


@pytest.mark.parametrize(
    "source, expected",
    [
        ("-1", -1),
        ("+5", 5),
        ("-1 + 5", 4),
        ("-(3 + 4)", -7),
        ("-2 * 3", -6),
        ("2 * -3", -6),
    ],
)
def test_unary_ops(source, expected: int):
    result = eval_str(source)
    _log(source, result)
    assert isinstance(result, ExprRes)
    assert result.value == expected


# ============================================================
# 括号表达式
# ============================================================


@pytest.mark.parametrize(
    "source, expected",
    [
        ("(1)", 1),
        ("((1))", 1),
        ("(1 + 2)", 3),
        ("((1 + 2))", 3),
        ("(1 + 2) * (3 + 4)", 21),
        ("((1 + 2) * 3)", 9),
    ],
)
def test_group(source, expected: int):
    result = eval_str(source)
    _log(source, result)
    assert isinstance(result, ExprRes)
    assert result.value == expected


# ============================================================
# 骰子表达式
# ============================================================


def test_dice_basic():
    """1d6 的结果应在 [1, 6] 范围内"""
    result = eval_str("1d6")
    _log("1d6", result)
    assert isinstance(result, ExprRes)
    assert 1 <= result.value <= 6


def test_dice_multiple():
    """3d6 的结果应在 [3, 18] 范围内"""
    result = eval_str("3d6")
    _log("3d6", result)
    assert isinstance(result, ExprRes)
    assert 3 <= result.value <= 18


def test_dice_deterministic():
    """固定种子下骰子结果确定"""
    rng = random.Random(42)
    result1 = eval_str("2d6", rng=rng)
    rng2 = random.Random(42)
    result2 = eval_str("2d6", rng=rng2)
    assert isinstance(result1, ExprRes)
    assert isinstance(result2, ExprRes)
    assert result1.value == result2.value


def test_dice_in_expression():
    """骰子在表达式中的混合运算"""
    result = eval_str("1d1 + 5")
    _log("1d1 + 5", result)
    assert isinstance(result, ExprRes)
    assert result.value == 6  # 1d1 必定为 1


def test_dice_sides_1():
    """1d1 始终为 1"""
    result = eval_str("4d1")
    _log("4d1", result)
    assert isinstance(result, ExprRes)
    assert result.value == 4


def test_dice_with_arithmetic():
    """骰子与算术的复合"""
    # 1d1 = 1, 1 + 2 * 1d1 = 1 + 2*1 = 3
    result = eval_str("1 + 2 * 1d1")
    _log("1 + 2 * 1d1", result)
    assert isinstance(result, ExprRes)
    assert result.value == 3


def test_dice_range_large():
    """较大面数骰子的范围检查"""
    result = eval_str("1d100")
    _log("1d100", result)
    assert isinstance(result, ExprRes)
    assert 1 <= result.value <= 100


# ============================================================
# 化简步骤（to_str）
# ============================================================


def test_steps_basic():
    """验证化简步骤的数量和内容"""
    steps = eval_steps("1 + 2")
    _log("1 + 2 steps", steps)
    assert not isinstance(steps, DiceLangError)
    # 至少有原式和最终结果两步
    assert len(steps) >= 2
    assert steps[0] == "1 + 2"
    assert steps[-1] == "3"


def test_steps_nested():
    """嵌套表达式的化简步骤"""
    steps = eval_steps("1 + 2 * 3")
    _log("1 + 2 * 3 steps", steps)
    assert not isinstance(steps, DiceLangError)
    assert steps[0] == "1 + 2 * 3"
    assert steps[-1] == "7"


def test_steps_dice():
    """骰子表达式有化简步骤"""
    rng = random.Random(42)
    steps = eval_steps("2d1", rng=rng)
    _log("2d1 steps", steps)
    assert not isinstance(steps, DiceLangError)
    assert len(steps) >= 2
    assert steps[-1] == "2"


# ============================================================
# 复杂表达式
# ============================================================


@pytest.mark.parametrize(
    "source, expected",
    [
        ("1 + 2 + 3 + 4", 10),
        ("2 * 3 * 4", 24),
        ("100 / 3 / 3", 11),  # (100//3)//3 = 33//3 = 11
        ("2 ^ 3 + 4 * 5", 28),  # 8+20
        ("(2 + 3) * (4 + 5)", 45),
        ("((1 + 1) + 1) * ((1 + 1) + 1)", 9),
    ],
)
def test_complex_expressions(source, expected: int):
    result = eval_str(source)
    _log(source, result)
    assert isinstance(result, ExprRes)
    assert result.value == expected


# ============================================================
# 错误处理
# ============================================================


@pytest.mark.parametrize(
    "source",
    [
        "1 @ 2",  # 非法字符
        "1 +",  # 表达式不完整
    ],
)
def test_error_invalid_input(source):
    """非法输入应抛出某种 DiceLangError"""
    result = eval_str(source)
    _log(source, result)
    assert isinstance(result, DiceLangError)


# ============================================================
# Fuzzing 占位
# ============================================================


@pytest.mark.xfail(reason="待实现", strict=True, raises=DiceLangError)
def test_fuzzing_full():
    raise TodoError("test_fuzzing_full")
